import json, sys, urllib.parse, urllib.request
Q = [
 "A novel G protein-biased agonist at the delta opioid receptor with analgesic efficacy in models of chronic pain",
 "N,N-Diethyl-4-(phenylpiperidin-4-ylidenemethyl)benzamide: a novel, exceptionally selective, potent delta opioid receptor agonist with oral bioavailability and its analogues",
 "A continuous flow process using a sequence of microreactors with in-line IR analysis for the preparation of N,N-diethyl-4-(3-fluorophenylpiperidin-4-ylidenemethyl)benzamide",
 "A novel scalable synthesis of pramipexole",
 "Dopamine autoreceptor agonists: resolution and pharmacological activity of 2,6-diaminotetrahydrobenzothiazole",
 "Application and synthesis of thiazole ring in clinically approved drugs",
 "Piperidine: a versatile heterocyclic ring for developing pharmaceutical compounds",
 "Reductive amination of aldehydes and ketones with sodium triacetoxyborohydride. Studies on direct and indirect reductive amination procedures",
 "The medicinal chemist's toolbox: an analysis of reactions used in the pursuit of drug candidates",
 "Survey of GMP bulk reactions run in a research facility between 1985 and 2002",
 "Analysis of the reactions used for the preparation of drug candidate molecules",
 "Analysis of past and present synthetic methodologies on medicinal chemistry: where have all the new reactions gone",
 "Large-scale applications of transition metal-catalyzed couplings for the synthesis of pharmaceuticals",
 "Large-scale applications of amide coupling reagents for the synthesis of pharmaceuticals",
 "Explosive properties of 1-hydroxybenzotriazoles",
 "Using the right green yardstick: why process mass intensity is used in the pharmaceutical industry to drive more sustainable processes",
 "CHEM21 selection guide of classical- and less classical-solvents",
 "The E factor 25 years on: the rise of green chemistry and sustainability",
 "Aiming for the ideal synthesis",
 "Systematic synthesis design. 6. Yield analysis and convergency",
 "The art of meeting palladium specifications in active pharmaceutical ingredients produced by Pd-catalyzed reactions",
 "Chemical process research and development in the 21st century: challenges, strategies, and solutions from a pharma industry perspective",
 "Organic synthesis provides opportunities to transform drug discovery",
 "Salt selection and optimisation procedures for pharmaceutical new chemical entities",
 "Pharmaceutical quality by design: product and process development, understanding, and control",
 "Green chemistry tools to influence a medicinal chemistry and research chemistry based organisation",
]
for q in Q:
    u="https://api.crossref.org/works?rows=3&select=DOI,title,author,issued,container-title,volume,page&query.bibliographic="+urllib.parse.quote(q)
    try:
        j=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"refcheck (mailto:sandler.leon@gmail.com)"}),timeout=40))["message"]["items"]
    except Exception as e:
        print("ERR",q[:50],e); continue
    print("\n##",q[:90])
    for it in j[:2]:
        a=it.get("author",[{}]); a1=(a[0].get("family","?") if a else "?")
        print("  ",it["DOI"],"|",(it.get("title") or [""])[0][:100],"|",a1,len(a),"|",(it.get("issued",{}).get("date-parts",[[None]])[0][0]),"|",(it.get("container-title") or [""])[0][:30],it.get("volume"),it.get("page"))
