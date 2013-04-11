from parser import Parser # for now, just load yaml rules via Parser
import networkx as nx
from collections import namedtuple

ParserRule = namedtuple('ParserRule', ['production','prev_class','prev_tokens','tokens','next_tokens','next_class'])

ParserOutput = namedtuple('ParserOutput', ['matches','output']) 


class GraphParser:

     
    def __init__(self, yaml_file='', data=None, blank=' '):
        
        self.old_parser=Parser(yaml_file)
        rules = self.old_parser.rules
        self.rules = self.rules_to_tuple(rules)
        self.tokens = self.old_parser.tokens
        DG= self.make_graph()
        #print DG
        self.DG = DG
        self.blank = blank # what token is assumed at before and after tokens
    
    def rules_to_tuple(self,rules):
        new_rules = []
        for r in rules:
            pr = ParserRule(production = r['production'], 
                            prev_class = r.get('prev_class'),
                            prev_tokens = r.get('prev_tokens'),
                            tokens = r['tokens'],
                            next_tokens = r.get('next_tokens'),
                            next_class = r.get('next_class'))
            new_rules.append(pr)
        return tuple(new_rules)
        
    def tokenize(self,input):
        return self.old_parser.token_match_re.findall(input)

    def make_graph(self): # turns rules into graph
        DG = nx.DiGraph()
        DG.add_node(0,token=None) #base
        def found_token_at_node(t, n_id):
            for s in DG.successors(n_id):
        #        print s,DG[s]
                if DG.node[s].get('token')==t:
                    return s

            return None

        def weight_of_rule(r): # and here namedtuples get clunky? 
            weight=1 # start at one.
            if r.prev_class:
                weight+=1
            if r.prev_tokens:
                weight+=1
            if r.next_class:
                weight+=1
            if r.next_tokens:
                weight+=1
            return 1/weight # when we navigate, we will go from low to high in the edges, so we want the inverse of the weights

        token_nodes = []
        match_nodes = []
        for rule in self.rules:
            curr_node = 0
            for t in rule.tokens:
                found = found_token_at_node(t,curr_node)
                if found: 
                    curr_node = found
                    continue
                else:
                    new_node = len(DG.nodes()) 
                    DG.add_node(new_node, token=t)
                    token_nodes.append(new_node) # save in list to be used in drawing for labels, color, etc.
        #            print DG.node[new_node],t
                    DG.add_edge(curr_node,new_node,weight=0) # if not a match node, then no weight, so will try first
                    curr_node = new_node
                
            rule_weight = weight_of_rule(rule) # this will be 1/4 for 4 constraints, 1/3 for 3 constraints, etc.

            new_match_node = len(DG.nodes()) 
            DG.add_node(new_match_node, rule=rule, found=rule.production)
            match_nodes.append(new_match_node)
            DG.add_edge(curr_node, new_match_node, weight=rule_weight,rule=rule) # for now, just copy the rule into the edge and check from that
            #print DG[curr_node][new_match_node]
            #print 'added rule',rule
        return DG

    def match_rule(self,rule, tokens, token_i, level):
        #print "trying to match rule ",rule
        parser_tokens = self.tokens
        # level shows how far we have moved forward from token_i
        #print "trying rule ",rule
        (num_prev_tokens, num_next_tokens) = (0,0)
        if rule.prev_tokens:
            num_prev_tokens = len(rule.prev_tokens)
            start_i = token_i - len(rule.prev_tokens)

            if start_i < 0:
                return False
            for i in range(num_prev_tokens): # had some trouble will all here for some reason
                if not tokens[start_i+i]==rule.prev_tokens[i]:
                    return False
#        print "  passed prev tokens"
        if rule.prev_class:
            #print 'in prev_class'
            start_i = token_i - num_prev_tokens-1
            prev_token = ''
            if start_i < -1:
                return False
            if start_i == -1: # if just one past, send a 'blank'
                prev_token = self.blank
            else:
                prev_token = tokens[start_i]
            if not rule.prev_class in parser_tokens[prev_token]:
                return False
       # print "passed prev class"
        if rule.next_tokens:
            num_next_tokens = len(rule.next_tokens)
            start_i = token_i + level # 
            if start_i + num_next_tokens > len(tokens):
                #print 'too long'
                return False
            for i in range(num_next_tokens):
                if not tokens[start_i+i]==rule.next_tokens[i]:
                    return False
        #print " pased next tokns"
        if rule.next_class:
            start_i = token_i+level+num_next_tokens
            if start_i == len(tokens): # if one past
         #       print 'loading blank', self.blank
                next_token = self.blank # load blank
            else:
                next_token = tokens[start_i]
            if not rule.next_class in parser_tokens[next_token]:
          #      print 'could not find ', rule.next_class, 'in ',parser_tokens[next_token], ' were ',parser_tokens
                return False
    #        if start_i + num_next_tokens == len(tokens):  need to deal with this one, but can in next
      #  print "passed next_class"
        return True

    def match_first_at(self,tokens, token_i):
        #print "trying tokens ",tokens," at token_i",token_i

        
    #    level = 0 # tracks how far along we are. gets increased when find a token?
        
           
        def descend_node(curr_node, level):
            
            #print "descending ",curr_node," at level ",level, self.DG.node[curr_node]
                        
            #edges are sorted by weight
            #for e in self.DG.edges(curr_node, data=True):
             #   print "  edge here",e 
            for edge in sorted(list(self.DG.edges(curr_node, data=True)), key=lambda x:x[2]['weight'] ):
                #print 'at edge', edge, 
                #if token_i + level < len(tokens): 
                    #print ' looking for ', tokens[token_i+level]
                #else:
                    #print '  at end of string'
                next_node = edge[1]
                
                #print edge[2]

                if edge[2].get('rule'): # if the edge has a rule
                    
                    if self.match_rule(edge[2]['rule'], tokens, token_i,level)==False:
                        #print 'FAILED RULE'         
                        continue # skip it
                #i#    else:
                    
                        #print 'passed edge rule'#return edge[2]['rule']# return rule here#"MADE IT!",edge[1],edge[2]
                  #  ParserRule = namedtuple('ParserRule', ['production','prev_class','prev_tokens','tokens','next_tokens','next_class'])
       
                if self.DG.node[next_node].get('rule'): # matched nodes have found and rule
                    #print 'found what looking for'
                    return self.DG.node[next_node].get('rule')

                #    return 'found a rule'

                #print tokens, token_i, level, tokens[token_i]
                #print self.DG.node[next_node].get('token')       
                if token_i+level < len(tokens): # do not descend if at end of road
                        

                    if self.DG.node[next_node].get('token')==tokens[token_i+level]:
                
                        #print 'Found successor ',next_node, self.DG.node[next_node]
                        d =descend_node(next_node, level+1)
                        
                        if d:
                            return d
            
    # no matches
        
        return descend_node(0,0)        
    
    def parse(self,string):
        t_i = 0
        tkns = self.tokenize(string)
        output = ''
        matches = []
        while t_i < len(tkns):
            #print "IN PARSE AT ",t_i, " of ",tkns
            m = self.match_first_at(tkns, t_i)
            #:w
            #if m == None:
                #print "error, no match  at ",t_i," in ",tkns
                #print "tkns[t_i} is", tkns[t_i]
                #print "string = ", string
                #print "matches = ",matches 
            assert m != None # for now, croak on error
            matches.append(m)
            output+=m.production
            t_i += len(m.tokens)
        return ParserOutput(output=output,matches=matches)
    
    def match_all_at(self,tokens, token_i):
        #print "trying tokens ",tokens," at token_i",token_i

        
    #    level = 0 # tracks how far along we are. gets increased when find a token?
        
        matches = []

        def descend_node(curr_node, level):
            
            #print "descending ",curr_node," at level ",level
            
            #edges are sorted by weight
            for edge in sorted(list(self.DG.edges(curr_node, data=True)), key=lambda x:x[2]['weight'] ):
                
                #print 'at edge', edge
                
                next_node = edge[1]
                
                #print edge[2]

                if edge[2].get('rule'): # if the edge has a rule
                    
                    if self.match_rule(edge[2]['rule'], tokens, token_i,level)==False:
                        continue
                    #else:
                    #    print 'passed edge rule'#return edge[2]['rule']# return rule here#"MADE IT!",edge[1],edge[2]
                  #  ParserRule = namedtuple('ParserRule', ['production','prev_class','prev_tokens','tokens','next_tokens','next_class'])
       
                if self.DG.node[next_node].get('rule'): # matched nodes have found and rule
                            matches.append(self.DG.node[next_node].get('rule'))
                            continue
                #    return 'found a rule'

                #else:
                    #print tokens, token_i, level
                
                if token_i+level < len(tokens):
                        
                        if self.DG.node[next_node].get('token')==tokens[token_i+level]:
                
                            #print 'Found successor ',next_node, self.DG.node[next_node]
                            
                            descend_node(next_node, level+1)
            
    # no matches
        
        descend_node(0,0)        
        return matches
    
#def draw_parser_graph(g):
#    pos=nx.spring_layout(g)
#    import matplotlib.pyplot as plt 
#    
#    plt.figure(figsize=(15,15))
#
#    labels = {}
#    for n,d in g.nodes(data=True):
#        label = ''
#        if d.get('token'):
#            label = d['token']
#        elif d.get('found'):
#            label = d['found']
#        labels[n] = label
#    colors = {}
#    
#        for n,d in g.nodes(data=True):
#            color=''
#            if d.get('token'):
#                color = '#A0CBE2'
#            elif d.get('found'):
#                color = '#E2CBA0'
#            colors[n] = color
            
    #    labels=dict((n,d['token']) for n,d in g.nodes(data=True)) # need to change labels for 0,1,etc.

        
#    nx.draw(g,labels=labels,node_color='#2CBACB',node_size=400)

def draw_parser_graph(g):
    num_nodes = len(g.nodes())
    colors = [None]*num_nodes
    labels = {}#[None]*num_nodes
    node_sizes = [None]*num_nodes
    node_shapes = {}#['d']*num_nodes
    len(g.nodes())
    #for n,d in g.nodes(data=True)
    len(colors)

    for n,d in g.nodes(data=True):
        node_shapes[n] = 'd'
        if n==0:
            colors[n] = '#00FF00'
            labels[n] = 'Start'
            node_sizes[n] = 400

        elif d.get('token'):
            colors[n] = '#BA2CCB'
            labels[n] = d['token']
            node_sizes[n] = 600
        else:
            colors[n] = '#2CBAFB'
            labels[n] = d['found']
            node_sizes[n] = 300
    import matplotlib.pyplot as plt
    plt.figure(figsize=(15,15))


    nx.draw(g,#node_size=node_sizes,#[G.population[v] for v in H],
            node_color=colors,node_size=node_sizes,node_shape='o',#node_shapes,
            edge_color='#A0A0A0',font_size=10,
            labels=labels)

if __name__ == '__main__':
    gp = GraphParser('settings/short.yaml')
    #r=ParserRule(production='s_z', prev_class=None, prev_tokens=('b','c'), tokens=('z'), next_tokens=None, next_class=None)
    #ts = ['b','c','z']
    #assert gp.match_rule(r,ts,2,1)
#    tkns =  ['b', 'c', 's', 'c', 'c','b']
    #print gp.DG.node[0]
    #print gp.match_first_at(ts,0)
    sp = GraphParser('settings/short.yaml')
    lp = GraphParser('settings/long.yaml')

    pp = GraphParser('settings/urdu-meter.yaml')
    s = ' muu-e aatish-diidah hai ;halqah mirii zanjiir kaa'
   # print pp.parse(s).output
    tkns = pp.tokenize(' ko))ii')
    print tkns
    #print pp.match_first_at(tkns,1)
    #print pp.rules
#    print pp.parse(' ko))ii')
    #tkns=[' ', 'm', 'uu', '-e', ' ', 'aa', 't', 'i', 'sh', '-', 'd', 'ii', 'd', 'a', 'h', ' ', 'h', 'ai', ' ', ';h', 'a', 'l', 'q', 'a', 'h', ' ', 'm', 'i', 'r', 'ii', ' ', 'z', 'a', 'n', 'j', 'ii', 'r', ' ', 'k', 'aa']
    
   # print sp.match_all_at(tkns,2)
    #print '---'
    #print lp.match_all_at(tkns,2)
    #parse = gp.parse(' par')# pyuu')#
   # siyaahii jaise gir jaave dam-e ta;hriir kaa;ga;z par')
    #print parse.output
    #gp = GraphParser('settings/short.yaml')
