from src.interface import create_demo_library, save_library, load_library, export_library_csv
from src.models import Bibliotheque

def test_create_and_save_load(tmp_path):
    b = create_demo_library()
    assert isinstance(b, Bibliotheque)
    p = tmp_path / "demo.json"
    save_library(b, str(p))
    b2 = load_library(str(p))
    assert len(b2.livres) == len(b.livres)
    csvp = tmp_path / "demo.csv"
    export_library_csv(b2, str(csvp))
    assert csvp.exists()
