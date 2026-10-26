import json, sys
sys.stdout.reconfigure(encoding="utf-8")
L = json.load(open("legends_lt.json", encoding="utf-8"))
for l in L:
    if l["claim"].startswith("Slaptame angare"):
        l["verdict"] = "IŠ DALIES"
        l["reveal"] = ("Pusiau taip. Vietinis gyventojas Stanislovas Puidokas pasakoja, kad kas buvo angare, niekas nežinojo, o gandų buvo visokių – ir apie raketų galvutes [T1]. "
                       "Oficialus Žemaitijos nacionalinio parko direkcijos šaltinis patvirtina, kad 8 raketų galvutės buvo saugomos karinės bazės sandėlyje [S1]. "
                       "Bet ar tai buvo būtent tas slaptas angaras – šaltiniai nesako. Galvutės čia buvo, o angaro paslaptis lieka neatskleista.")
        l["evidence"].append({"source": "S1", "quote": "8 raketų galvutės (branduoliniai užtaisai) buvo saugomos karinės bazės sandėlyje"})
        l["edited_by_hand"] = True
    if l["claim"].startswith("Iš Plokštinės bazės po mišku"):
        l["verdict"] = "NEĮRODYTA"
        l["reveal"] = ("Šito niekas nėra įrodęs. Buvęs veterinaras ir kolūkio pirmininkas Stanislovas Mikašauskas medžiodavo su bazės karininkais, bet apie bazę jie tylėdavo [T2]. "
                       "Apie tunelius, sako jis, kalbėjo kai kas, tačiau pats abejoja: jei jie būtų buvę, kas nors jais būtų pravažiavęs [T2]. "
                       "Oficialūs šaltiniai mini tik požeminių koridorių tinklą, jungusį bazės patalpas [S3]. Ilgi tuneliai po mišku kol kas lieka gandu.")
        l["evidence"].append({"source": "S3", "quote": "Įvairias patalpas jungė požeminių koridorių tinklas"})
        l["sources"] = ["T2", "S3"]
        l["edited_by_hand"] = True
json.dump(L, open("legends_lt.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("fixed")
