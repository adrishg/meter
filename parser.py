import re


def load_yaml(filename):
    """
    Reads any yaml file and returns it as object.
    """
    import yaml
    stream = file(filename)
    return yaml.load(stream)

debug=False

def compare_rules(x,y):
    """
    Compares parser rules and sees which has more tokens or conditions (prev, next)
    """
    diff = len(y['tokens'])-len(x['tokens'])
    if diff != 0:
        return diff
    (x_conds, y_conds) = (0,0)
    for cond in ('prev','next'):
        if cond in x: x_conds +=len(cond)
        if cond in y: y_conds +=len(cond)
    for cond in ('prev_class', 'next_class'):
        if cond in x: x_conds += 1
        if cond in y: y_conds += 1
    return y_conds - x_conds # see if one has  more <classes>


def rules_from_yaml_data(rules_raw):
    """
    Returns sorted and usable parser rules from yaml file. 

    rules_raw is a dictionary (loaded from yaml):
        key: <previous token class> token token <next token class> 
        value: production

    previous class and next class of token are optional. 
    The production allows \N{unicode char name} strings.

    Output of return is list of rules containing:
        prev_class: previous token class [optional, will look behind prev]
        prev:       previous tokens [optional]
        tokens:     list of tokens
        next:       next token class [optional]
        next_class: next token class [optional, will look ahead of next]
        production: string production

    Example: (<wb> a b c) d (e f <wb>): \N{LATIN SMALL LETTER D}

    """
    
    import unicodedata
    def unescape_unicode_charnames(s):
        """
        Takes \N{charname} in production rule and turns to Unicode string.
        """
        
        def get_unicode_char(matchobj):
            """
            Returns Unicode character of \N{character name}
            """
            s = matchobj.group(0)
            m = re.match(r'\\N{(.+)}',s)
            char = unicodedata.lookup(m.group(1))
            return char
    
        return re.sub(r'\\N{.+?}',get_unicode_char,s)

        # load and prepare rules
    
    rules = [] # clean list of rule
#    print "rules_r is"+str(rules_raw)
    for key in rules_raw:
        if debug: print "key is "+key+" = "+rules_raw[key]
        rule = {}           #1       #2        #3
        s  ='(?:'   
        s +='\('
        s +='(?:\s?<(.+?)> )?' # group 1, prev class (in brackets indicating cluster)
        s +='(.+?)\s?' # group 2, prev tokens (to be split)
        s +='\) '
        s +='|' # either a cluster or a particular previous class (Could add additional support, e.g. class or paretic.
        s +='<(.+?)> ' # group 3, prev class (not in cluster)
        s +=')?'
        s += '(.+?)' # group 4, tokens
        s += '(?:' # cluster for following tokens, clusters 
        s += ' \('
        s += '\s?(.+?)' # group 5, next tokens
        s += '(?: <(.+?)>)?' # group 6, next class
        s += '\s?\)'
        s += '|'
        s += ' <(.+?)>' # group 7, follo
        s += ')?$'
        m = re.match (s, key, re.S)
        assert (m is not None)
        if m.group(1): rule['prev_class'] = m.group(1)
        if m.group(2): rule['prev_tokens'] = m.group(2).split(' ')
        if m.group(3): rule['prev_class'] = m.group(3)
        if m.group(4)==' ':
            rule['tokens'] = [' '] #ugh--missed this one.
        else:
            rule['tokens'] = m.group(4).split(' ')
        if m.group(5): rule['next_tokens'] = m.group(5).split(' ')
        if m.group(6): rule['next_class'] = m.group(6)
        if m.group(7): rule['next_class'] = m.group(7) 
     
        rule['production'] = unescape_unicode_charnames(rules_raw[key])
        if debug:print rule
        if debug:print '----'
        rules.append(rule)

    return rules

debug=False
class Parser:
    error_on_last = False
    last_string = ''
    error_string = ''

    def __init__(self, yaml_file='', data=None):
        
        if yaml_file != '':
            data = load_yaml(yaml_file)
        else: 
            assert data is not None
        self.rules = rules_from_yaml_data(data['rules']) # specifically YAML here
        rules = self.rules
        rules.sort(cmp=compare_rules)
        self.tokens = data['tokens']
        self.token_match_re = self.generate_token_match_re()


    def generate_token_match_string(self):
        tokens = self.tokens.keys()
        sorted_tokens = sorted(tokens, key=len, reverse=True)
        escaped_tokens = map(re.escape, sorted_tokens)
        tokens_re_string = '|'.join(escaped_tokens)+'|.' # grab unknowns
        return tokens_re_string

    def generate_token_match_re(self):
        '''
        Create regular expression from Parser.tokens sorted by length

        Adds final "." in case nothing found
        '''

        tokens = self.tokens.keys()
        sorted_tokens = sorted(tokens, key=len, reverse=True)
        escaped_tokens = map(re.escape, sorted_tokens)
        tokens_re_string = '|'.join(escaped_tokens)+'|.' # grab unknowns
        return re.compile(tokens_re_string, re.S)

    def tokenize(self,input):
        return self.token_match_re.findall(input)

    def parse(self,input,on_error='',on_error_additional='',return_all_matches=False, debug=False):
        #reset error-catching variables
        self.last_string = input
        self.error_string = ''
        self.error_on_last = False
        self.parse_details = []

        output = ''
        tkns = self.token_match_re.findall(input)
        t_i = 0              # t_i counter for token position in list
        while t_i<len(tkns): # while in range of tokens in string
            matched = False
            for rule_id,rule in enumerate(self.rules):
                try:
                    r_tkns = []
                    if ('prev_tokens' in rule): 
                        i_start = t_i-len(rule['prev_tokens'])
                        r_tkns += rule['prev_tokens']
                        #'print problem in '+str(rule)
                    else:
                        i_start = t_i
                    r_tkns +=rule['tokens']                
                    if 'next_tokens' in rule:
                        r_tkns += rule['next_tokens']
                    if all(r_tkns[i] == tkns[i_start+i] for i in range(len(r_tkns)) ):
                        if 'prev_class' in rule: # if rule has a prev class
                            if i_start==0: 
                                # if at start of string, allow for word break
                                prev_token = ' '
                            else:
                                prev_token = tkns[i_start-1]                            
                            if not(rule['prev_class'] in self.tokens[prev_token]):
                                continue
                        if 'next_class' in rule:
                            if i_start+len(r_tkns)==len(tkns): # if end of string
                                next_token = ' '
                            else:
                                next_token = tkns[i_start+len(r_tkns)]
                            if not next_token in self.tokens:
                                next_token = ' ' # in case it's missing (SHOULD THIS BE ADDED ABOVE?)
                            if not(rule['next_class'] in self.tokens[next_token]):
                                continue
                        # We did it!
                        if debug==True:
                            print "matched "+str(rule)
                        matched = True
                        output += rule['production']
                        self.parse_details.append({'tokens':rule['tokens'], 'start':t_i, 'rule':rule, 'rule_id':rule_id})
                        t_i += len(rule['tokens']) 
                        break
                except IndexError:
                    continue
            if matched==False:
                import unicodedata
                curr_error = 'no match at token # '+str(t_i)+': '+tkns[t_i]+" "
                try:
                  for c in tkns[t_i]:
                    curr_error += unicodedata.name(unichr(ord(c)))+" "
                except TypeError:
                  curr_error += "TYPE ERROR HERE!!!!"
                curr_error += ' [' + on_error_additional + ']'
                if on_error=='print':
                    print curr_error
                self.error_on_last = True
                self.error_string +=curr_error+"\n"
                self.parse_details.append({'tokens':tkns[t_i], 'start':t_i, 'rule':None}) # save error
                prev_token=' ' # reset
                t_i += 1
        return output

    def match_all_at(self,tkns,t_i):
        """
        
        Finds all matches at a particular token_index (t_i) 
        
        Returns {rule_id: id for rule, 
                 start: index of match (from token array),
                 tokens: tokens matched,?
                 production: production ? }
        """
        matches = ''
        output = []
        for rule_id,rule in enumerate(self.rules):
            try:
                r_tkns = [] # array of all tokens to match (including rule's [prev_tokens]&[next_tokens]
                if ('prev_tokens' in rule):
                    i_start = t_i-len(rule['prev_tokens'])
                    r_tkns += rule['prev_tokens']
                else:
                    i_start = t_i
                r_tkns +=rule['tokens']
                if 'next_tokens' in rule:
                    r_tkns += rule['next_tokens']
                if all(r_tkns[i] == tkns[i_start+i] for i in range(len(r_tkns)) ):
                    if 'prev_class' in rule: # if rule has a prev class
                        if i_start==0:
                            # if at start of string, allow for word break
                            prev_token = 'b'
                        else:
                            prev_token = tkns[i_start-1]
                        if not(rule['prev_class'] in self.tokens[prev_token]):
                            continue
                    if 'next_class' in rule:
                        if i_start+len(r_tkns)==len(tkns): # if end of string
                            next_token = 'b'
                        else:
                            next_token = tkns[i_start+len(r_tkns)]
                        if not next_token in self.tokens:
                            next_token = 'b' # in case it's missing (SHOULD THIS BE ADDED ABOVE?)
                        if not(rule['next_class'] in self.tokens[next_token]):
                            continue
                    # We did it!
                    matched = True
                    output.append( {'rule_id':rule_id, 'tokens':rule['tokens'], 'start': t_i, 'rule':rule} )
                    
            except IndexError:
                continue
        return output
    
if __name__ == '__main__':
    import pdb
    p = Parser('settings/urdu-meter.yaml')
    import pprint
    pprint.pprint(p.rules)
    print p.tokenize(' dal-daaz')
