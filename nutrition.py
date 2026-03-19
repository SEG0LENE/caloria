import openai
import json

def analyser_repas(client: openai.OpenAI, texte: str) -> dict:
    prompt = f"""Tu es un nutritionniste expert en cuisine française.
Analyse ce repas : "{texte}"
Estime les quantités selon les portions standard françaises.
Réponds UNIQUEMENT avec ce JSON :
{{
  "aliments": [{{"nom": "Nom", "quantite_g": 150, "calories": 210}}],
  "total_calories": 450,
  "fiabilite": "haute",
  "hypotheses": "Courte phrase sur les hypothèses."
}}
fiabilite : haute / moyenne / basse"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return json.loads(resp.choices[0].message.content)

def conseil_du_jour(client: openai.OpenAI, repas: list, objectif: int) -> str:
    if not repas:
        return "Aucun repas enregistré. Commence par décrire ce que tu as mangé !"
    total = sum(r.get("total_calories", 0) for r in repas)
    aliments = [a.get("nom", "") for r in repas for a in r.get("aliments", [])]
    prompt = f"""Nutritionniste bienveillant.
Calories : {total} kcal (objectif : {objectif} kcal)
Aliments : {", ".join(aliments)}
Donne un conseil court (3-4 phrases), positif et concret. En français."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content