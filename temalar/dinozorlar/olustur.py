# -*- coding: utf-8 -*-
"""
Dinozorlar puzzle — 450 x 250 mm, 6 parça.

Varlıklar katmanlı gelir: parçasız sahne + her dinozor magenta zeminde.
Tüm üretim ortak motorda: ../_ortak/puzzle_motoru.py

Çalıştırma:  python3 olustur.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "_ortak"))
from puzzle_motoru import Parca, Tema, uret        # noqa: E402

KLASOR = os.path.dirname(os.path.abspath(__file__))

# Sahnede zemin (kum düzlüğü) yaklaşık y=126 mm'de başlar; arka sıra dinozorlar
# ayakları y~132'ye, ön sıra y~236'ya basacak şekilde konumlandı. Ön sıra
# derinlik hissi için biraz daha iri.
T = Tema(
    ad="dinozorlar",
    baslik="DINOZORLAR PUZZLE",
    klasor=KLASOR,
    parcalar=[
        # --- arka sıra (daha küçük, uzakta)
        Parca("trex", "T-Rex", "T-Rex",
              merkez=(110, 94), genislik=90),
        Parca("triceratops", "Triceratops", "Triceratops",
              merkez=(235, 102), genislik=90),
        Parca("stegosaurus", "Stegosaurus", "Stegosaurus",
              merkez=(358, 103), genislik=90),
        # --- ön sıra (daha iri, yakında)
        Parca("brontozor", "Brontozor", "Brontosaurus",
              merkez=(95, 192), genislik=105),
        Parca("velosiraptor", "Velosiraptor", "Velociraptor",
              merkez=(225, 199), genislik=105),
        Parca("parasaurolophus", "Parasaurolophus", "Parasaurolophus",
              merkez=(355, 196), genislik=105),
    ])

if __name__ == "__main__":
    uret(T)
