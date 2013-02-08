from parser import Parser
import re
import pdb

debug=False

def load_yaml(filename):
    """
    Reads any yaml file and returns it as object.
    """
    import yaml
    stream = file(filename)
    return yaml.load(stream)

class Scanner: 
    """
    Handles metrically scansion.
    """
    def __init__(self, meter_file = 'settings/urdu-meter.yaml', #terrible name for this
                       short_file='settings/short.yaml', 
                       long_file='settings/long.yaml', 
                       meters_file = 'settings/gh-meters.yaml',
                       meter_description_file='settings/gh-reference.yaml'):
        self.pp = Parser(meter_file)
        self.sp = Parser(short_file)
        self.lp = Parser(long_file)
        self.meters_with_feet = load_yaml(meters_file)
        self.meters_without_feet = {}#load_yaml(gh_meters_file)
        for i,v in self.meters_with_feet.iteritems():
            new_i = i.replace('/','')
            self.meters_without_feet[new_i] = i # save a list for later
        self.ok_meters_re = '|'.join(self.meters_without_feet)
        self.meter_descriptions = load_yaml(meter_description_file)

    def meter_ok(self, so_far):
        return re.search('(?:^|\|)'+so_far, self.ok_meters_re)

    def bad_combo(self,prev_matches, this_match):
        try:
            prev_match = prev_matches[-1]
            for (p_m,t_m) in [('s_bcsc','l_v'), #need expand these
                              ('l_csc','l_v'), 
                              ('l_bsc','s_v(b)'),
                              ('l_bsc', 'l_v'),
                              ('s_c', 'l_v'),
                              ('s_c', 'l_v<ii+z>'),
                              ('s_c', 'l_z'),
                              ('s_c', 's_v(b)'),
                              ('s_c', 's_c<h+wb>'),##c s       c<h+wb>
                              ('s_bcs', 's_c'),#b c s     c<h+wb> 
                              ('s_bcs', 's_c<h+wb>'),
                              ('s_cs',  's_c<h+wb>'),
                              ('s_bs', 's_c'), 
                              ('s_cs', 's_c')]:

                if prev_match['rule']['production']==p_m and this_match['rule']['production']==t_m: 
                    return True
        except IndexError:
            pass
        return False
    
    def scan(self, s, known_only=False, debug=False, parser_debug = False):
        pp = self.pp # Parser("urdu-meter.yaml")
        sp = self.sp # Parser('short.yaml')
        lp = self.lp # Parser('long.yaml')
        sss = pp.parse(s, debug = parser_debug)    
        if debug:
            import pprint
            ppr = pprint.PrettyPrinter(indent=4)
            ppr.pprint( sss)
        self.pd = pp.parse_details # save info about tokens here
        if debug:
            print self.pd
        tkns= lp.tokenize(sss) # now tokenize that--problem here w/ kyaa
        if debug:
            print tkns
        match_results = [{'matches':[], 'index':0}]
        final_results = []

        while (len(match_results)>0):
            mr = match_results.pop()
            for p in (sp, lp):  # go through short and long parsers
                newMatches = p.match_all_at(tkns, mr['index'])
                if len(newMatches)==0: continue # move along if no matches
                for m in newMatches:
                    if self.bad_combo(mr['matches'],m): # remove unacceptable combinations
                        continue
                    new_index = mr['index'] + len(m['tokens'])
                    new_matches = list(mr['matches']) # have to make a copy of the matches here
                    if re.match('l_', m['rule']['production']):
                        meter_string = '='
                    elif re.match('s_', m['rule']['production']):
                        meter_string = '-'
                    else:
                        meter_string = '?'
                    m['meter_string'] = meter_string
                    new_matches.append(m)
                    new_mr = { 'matches': new_matches, 'index': new_index, 'meter_string':meter_string}
                    scan_line = ''
                    for m in new_matches:
                            scan_line +=m['meter_string']
                    new_mr['scan'] = scan_line
                    if (known_only==True) and not (self.meter_ok(scan_line)):
                        #print "Bad meter: "+scan_line
                        continue
                    if new_index==len(tkns) or (new_index+1==len(tkns) and tkns[-1]=='b'):
                        if (known_only==True) and not (scan_line in self.meters_without_feet):
                            # in case meter is okay until now but not complete
                            continue
                        final_results.append(new_mr)
                        continue
                    else:
                        match_results.append(new_mr)
        if debug:
            pprint.pprint(final_results)
        return ({'results':final_results, 'orig_parse':self.pd, 'tkns':tkns})
    def quick_results(self, scan_results):
        final_results = scan_results['results']
        scan_lines=[]
        for r in final_results:
            scan_line = "( "
            for m in r['matches']:
                scan_line += m['meter_string']+' '
            scan_line += ")"
            scan_lines.append(scan_line)
        return ' '.join(scan_lines)

           
    def print_scan(self,scan_results, details=False, known_only = False,no_tkns = False, no_numbers=False, no_orig_tkns=False):
        meters = self.meters_without_feet#load_yaml('gh-meters.yaml')
        final_results = scan_results['results']
        final_results = sorted(final_results, key=lambda k: k['scan']) # sort by scan
        pd = scan_results['orig_parse'] # parser detail of original scan (preserves original tokens)
        tkns = scan_results['tkns'] # tokens of second-level parser
        #pdb.set_trace()
        for i, r in enumerate(final_results):
            if known_only and (not (r['scan'] in meters)):
                continue
            if no_numbers==False: print 'result #'+str(i)#+ i#" "+meter_string
            if (r['scan'] in meters):
                meter_with_feet = self.meters_without_feet[r['scan']]
                meter_id = self.meters_with_feet[meter_with_feet]
                meter_description = self.meter_descriptions[meter_id]
                print 'matches '+meter_description+' <'+meter_id+'> as '+meter_with_feet
            scan_line = ''
            tkn_line  = ''
            orig_tkn_line = ''
            
            for m in r['matches']:
                scan_line += m['meter_string'].ljust(10)
                tkn_line += ' '.join(m['tokens']).ljust(10)
                orig_tkns = ''
                for t in pd[m['start']:(m['start']+len(m['tokens']))]:
                  orig_tkns += ' '.join(t['tokens'])
                orig_tkn_line += orig_tkns.ljust(10)
            print scan_line
            if no_tkns == False:
                print tkn_line
            if no_orig_tkns == False:
                print orig_tkn_line
    


'''
G1: =-==/=-==/=-==/=-=(-)
G10: ==-/=-==(-)//==-/=-==(-)
G11: '[-|=]-==/--==/[--|=]=(-)'
G12: -==/-==/-==/-==(-)
G13: ==-/-==-/-==-/`-==(-)
G14: =-==/=-==/=-=(-)
G15: =--=/-=-=(-)//=--=/-=-=(-)
G16: -=-=/--==/-=-=/--==(-)
G17: =--=/=-=-/=--=/=(-)
G18: ==-/-===(-)//==-/-===(-)
G19: '==[=/|-/-]=-=/-==(-)'
G2: -===/-===/-===/-===(-)
G3: ==-/=-=-/-==-/=-=(-)
G4: =-=/-===(-)/=-=/-===(-)
G5: '[-|=]-==/--==/--==/[--|=]=(-)'
G6: --=-/=-==/--=-/=-==(-)
G7: -===/-===/-==(-)
G8: '[=|-]-==/-=-=/[--|=]=(-)'
G9: '-=-=/--==/-=-=/[--|=]=(-)'
'''

if __name__ == '__main__':
    s = Scanner()
    _ = " ;xvush uuftaadagii kih bah .sa;hraa-e inti:zaar"
    _ = " dil-e har qa:trah hai saaz-e anaa al-ba;hr"#-e .sadaa paayaa"#dekhiye laatii hai us sho;x kii na;xvat kyaa rang"# le ga))ii saaqii kii na;xvat qulzum-aashaamii mirii"# ;husn aur us pah ;husn-e :zann rah ga))ii buu al-havas kii sharm"
    _ = " dekhiye laatii hai us sho;x kii na;xvat kyaa rang"#vaa;n vuh farq-e naaz ma;hv-e baalish-e kam;xvaab thaa"#lab pardah-sanj-e zamzamah-e al-amaa;n nahii;n"
    #      =   =  -   =  -   =  - = -  =  - = - =
    #          == -  /=  -   =  -/-=  = -/=-=(-)
    _ = " ;gara.z shast-e but-e naavuk-figan kii aazmaa))ish hai"
    pdb.set_trace()
    scn = s.scan(_, known_only=False, debug=True)
    pd = s.pd
    print s.print_scan(scn)
    print "****"
    print s.print_scan(scn, known_only=True)
   # _ = " ko))ii"
    #_ = " dar pardah unhe;n ;gair se hai rab:t-e nihaanii" #bol kih lab aazaad hai tere"#ham ne dil khol ke daryaa ko bhii saa;hil baa;ndhaa"#vaa;n pahu;nch kar jo ;gash aataa pa))e-ham hai ham ko"
    #_ = " kamaal-e garmii-e sa((ii-e talaash-e diid nah puuchh"
    #_ = " aashiyaanah"
    #_ = _.lower()
    #scn = s.scan(_,knownOnly=False, debug=True)
    #pd = s.pd
    #print s.quick_results(scn)#print_scan(scn)

    #die
    lines = tuple(open('bad-gh.txt', 'r'))

    mylines = [lines[0]]
    for _ in lines:
        _ = _.strip()
        m = re.match('(.+?)\s+(.+?)\s+([G]\d+)$', _)
        id = m.group(1)
        verse =  m.group(2)
        #print "********************* "+_
        meter =  m.group(3)
        scn = s.scan(verse,debug=False,known_only=True)
        if not s['results']:
            print "NOO!!!!!"
            print verse
            scn = s.scan(verse,known_only=False)
            pd = s.pd
            print s.print_scan(scn)#scn)#.print_scan(scn, knownOnly=False)
        else:
            print "YES! "+verse