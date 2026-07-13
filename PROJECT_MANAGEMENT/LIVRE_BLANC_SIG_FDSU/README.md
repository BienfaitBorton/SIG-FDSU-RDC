# Production du Livre Blanc SIG-FDSU RDC

Ce dossier contient le brouillon institutionnel du Livre Blanc officiel du SIG-FDSU RDC.

## Contenu

| Élément | Rôle |
|---|---|
| `01_LIVRE_BLANC_SIG_FDSU_RDC.md` | Manuscrit principal |
| `diagrams/` | Sources Mermaid réutilisables |
| `figures/` | Registre et futurs visuels validés |
| `references/` | Méthode de citation et références |

## Conversion DOCX

La conversion peut être réalisée avec [Pandoc](https://pandoc.org/), après validation du contenu :

```powershell
pandoc ".\01_LIVRE_BLANC_SIG_FDSU_RDC.md" `
  --from markdown `
  --to docx `
  --toc `
  --number-sections `
  --reference-doc ".\references\modele_word_fdsu.docx" `
  --output ".\SIG-FDSU_RDC_Livre_Blanc_v1.0.docx"
```

`modele_word_fdsu.docx` est volontairement absent : il doit être fourni ou validé par le FDSU avant diffusion. Il définira la couverture, les styles de titres, les en-têtes/pieds de page, la numérotation, la police et la charte graphique institutionnelle.

## Conversion PDF

Après validation de la charte graphique :

```powershell
pandoc ".\01_LIVRE_BLANC_SIG_FDSU_RDC.md" `
  --from markdown `
  --pdf-engine=xelatex `
  --toc `
  --number-sections `
  --output ".\SIG-FDSU_RDC_Livre_Blanc_v1.0.pdf"
```

Pour un PDF institutionnel, il est recommandé de convertir d’abord le DOCX validé, puis de produire le PDF depuis Word avec le modèle institutionnel approuvé.

## Consignes de publication

1. Faire valider les auteurs, la classification et la préface officielle.
2. Vérifier chaque affirmation factuelle et chaque référence externe.
3. Remplacer les emplacements de figures par des visuels validés, non décoratifs et accompagnés d’une légende.
4. Générer le sommaire, la liste des figures et les numéros de pages dans le document final.
5. Obtenir la validation institutionnelle avant diffusion.

Le Markdown est le master éditorial. Les formats DOCX et PDF sont des publications dérivées.
