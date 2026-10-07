import json, urllib.parse, urllib.request
Q = [
 "Analysis of the structural diversity, substitution patterns, and frequency of nitrogen heterocycles among U.S. FDA approved pharmaceuticals",
 "Large-scale applications of transition metal-catalyzed couplings for the synthesis of pharmaceuticals Magano Dunetz Chemical Reviews 2011",
 "The medicinal chemist's toolbox: an analysis of reactions used in the pursuit of drug candidates Roughley Jordan Journal of Medicinal Chemistry 2011",
 "Discovery of ritonavir, a potent inhibitor of HIV protease with high oral bioavailability and clinical efficacy",
 "sodium triacetoxyborohydride reductive amination ethyl acetate replacement of 1,2-dichloroethane",
 "Amino acid-protecting groups Chemical Reviews Isidro-Llobet",
 "Application of continuous flow chemistry in pharmaceutical process development Baxendale",
 "Reaction calorimetry process safety scale-up exothermic Organic Process Research Development thermal hazard assessment",
 "Palladium removal from active pharmaceutical ingredients scavengers crystallization",
 "ICH Q3D elemental impurities palladium permitted daily exposure pharmaceutical",
 "Nicotinic and tetrahydrobenzothiazole pramipexole impurity synthesis dihydrochloride process",
 "supply chain concentration active pharmaceutical ingredients India China dependence drug shortages",
]
for q in Q:
    u="https://api.crossref.org/works?rows=3&select=DOI,title,author,issued,container-title,volume,page&query.bibliographic="+urllib.parse.quote(q)
    try:
        j=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"refcheck (mailto:sandler.leon@gmail.com)"}),timeout=40))["message"]["items"]
    except Exception as e:
        print("ERR",q[:50],e); continue
    print("\n##",q[:100])
    for it in j[:3]:
        a=it.get("author",[{}]); a1=(a[0].get("family","?") if a else "?")
        print("  ",it["DOI"],"|",(it.get("title") or [""])[0][:110],"|",a1,len(a),"|",(it.get("issued",{}).get("date-parts",[[None]])[0][0]),"|",(it.get("container-title") or [""])[0][:30],it.get("volume"),it.get("page"))
