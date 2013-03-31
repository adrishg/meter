from parser import Parser
import re
import pdb
import csv
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
                       bad_combos_file = 'settings/bad_combos.csv', # csv for this one
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
        self.bad_combos = []
        with open(bad_combos_file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar="'")
            for row in reader:
                assert len(row) == 2
                self.bad_combos.append(row)

    def meter_ok(self, so_far):
        return re.search('(?:^|\|)'+so_far, self.ok_meters_re)

    def bad_combo(self,prev_matches, this_match):
        '''
        Makes sure illegal metrical combinations are removed.
        '''
        try:
            prev_match = prev_matches[-1]
            for (p_m,t_m) in self.bad_combos:
                if prev_match['rule']['production']==p_m and this_match['rule']['production']==t_m: 
                    return True
        except IndexError:
            pass
        return False
    
    def scan(self, s, known_only=True, debug=False, parser_debug = False):
        """
        Scans an input string(s), ignoring unacceptable combinations if known_only set

        Returns a dictionary with ['results', 'tkns', 'orig_parse']

        results, a dictionary,  hold the details
            matches: list of dictionaries holding the match details
                tokens: tokens matching long or short (e.g. c,s,c)
                start: the index in the processed string
                rule_id: index for the rule (* needs to account for source)
                rule: copy of the rule (* don't need to copy with rule_id passed)
                meter_string: production of match (e.g. = or -)
            index: the last match (ignore, but used in scanning)
            meter_string: the last meter string (ignore, but used in scanning)
            scan: the cumulative meter string (e.g. =-===-===-===-=)
        
        tkns the tokens of the original input string (s)
        orig_parse hold the production of the tkns (used by the scanner)


        """
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
        """
        print quick results
        """
        final_results = scan_results['results']
        scan_lines=[]
        for r in final_results:
            scan_line = "( "
            for m in r['matches']:
                scan_line += m['meter_string']+' '
            scan_line += ")"
            scan_lines.append(scan_line)
        return ' '.join(scan_lines)

    def id_meter(self,scan_string):
        '''
        takes a scan string without feet, returns id, e.g. G1
        '''
        meter_with_feet = self.meters_without_feet[scan_string]
        meter_id = self.meters_with_feet[meter_with_feet]
        #meter_description = self.meter_descriptions[meter_id]
        return meter_id

    def describe_meter(self,scan_string):
        '''
        takes a scan string without feet, returns meter string with feet and variations
        '''
        meter_with_feet = self.meters_without_feet[scan_string]
        meter_id = self.meters_with_feet[meter_with_feet]
        meter_description = self.meter_descriptions[meter_id]
        return meter_description

    # todo: copy this into print_scan 
    def print_scan_result(self,r, orig_parse, details=False, known_only = False, no_description=False,
                          no_tkns = False, no_numbers=False, no_orig_tkns=False, no_match_production=False):
        '''
        takes a single scan result (r) and the orginal parse (of the tokens) as input
        '''
        scan_line = ''
        tkn_line  = ''
        orig_tkn_line = ''
        match_production_line = '' # eg l_bcsc
        if no_description == False:
            if (r['scan'] in self.meters_without_feet):
                meter_with_feet = self.meters_without_feet[r['scan']]
                meter_id = self.meters_with_feet[meter_with_feet]
                meter_description = self.meter_descriptions[meter_id]
                print 'matches '+meter_description+' <'+meter_id+'> as '+meter_with_feet

        for m in r['matches']:
            scan_line += m['meter_string'].ljust(10)
            tkn_line += ''.join(m['tokens']).ljust(10)
            orig_tkns = ''
            for t in orig_parse[m['start']:(m['start']+len(m['tokens']))]:
                orig_tkns += ''.join(t['tokens'])
            orig_tkn_line += orig_tkns.ljust(10)

            match_production_line +=m['rule']['production'].ljust(10)
            m
        print scan_line
        if no_tkns == False:
            print tkn_line
        if no_orig_tkns == False:
            print orig_tkn_line
        if no_match_production == False:
            print match_production_line
   
    def matched_meters(self, scan):
        '''
        Gives list of matched meters as meter id, e.g. ['G1','G2']
        '''
        print "** "
        print scan.keys()
        meters = self.meters_without_feet # acceptable meters
        final_results = scan['results']
        for i, r in enumerate(final_results):
            if (not(r['scan'] in meters)): # skip if no match 
                continue
            meter_id = self.meters_with_feet[meter_with_feet]
            results.append(meter_id)
        return results # return list of meters


    
    def print_scan(self,scan_results, details=False, no_tkns = False, no_numbers=False, no_orig_tkns=False,known_only=False,
                   no_match_production = True):
        meters = self.meters_without_feet#load_yaml('gh-meters.yaml')
        final_results = scan_results['results']
        final_results = sorted(final_results, key=lambda k: k['scan']) # sort by scan
        _orig_parse = scan_results['orig_parse'] # parser detail of original scan (preserves original tokens)
        tkns = scan_results['tkns'] # tokens of second-level parser
        #pdb.set_trace()
        for i, r in enumerate(final_results):
            if known_only and (not (r['scan'] in meters)): # allows override
                continue
            if no_numbers==False: print 'result #'+str(i)
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
                tkn_line += ''.join(m['tokens']).ljust(10)
                orig_tkns = ''
                for t in _orig_parse[m['start']:(m['start']+len(m['tokens']))]:
                  orig_tkns += ''.join(t['tokens'])
                orig_tkn_line += orig_tkns.ljust(10)
            print scan_line
            if no_tkns == False:
                print tkn_line
            if no_orig_tkns == False:
                print orig_tkn_line
    

if __name__ == '__main__':
    s = Scanner()
    _ = " ;xvush uuftaadagii kih bah .sa;hraa-e inti:zaar"
    _ = " ;gara.z shast-e but-e naavuk-figan kii aazmaa))ish hai"
    _ = "naqsh faryaadii hai kis kii sho;xii-e ta;hriir kaa"
    pdb.set_trace()
    scn = s.scan(_, known_only=True, debug=True)

    print s.matched_meters(scn)
    pd = s.pd
    print s.print_scan(scn)
    print s.print_scan_result(scn['results'][0], scn['orig_parse'])
    print s.meter_descriptions

    #print "****"
    print s.print_scan(scn, known_only=True)
    print scn.keys()
