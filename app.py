from io import BytesIO

from flask import Flask, jsonify, request, send_file, send_from_directory
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

app = Flask(__name__, static_folder=".", static_url_path="")


def smiles_to_svg(smiles: str, width: int = 900, height: int = 540) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Ugyldig SMILES-streng.")

    AllChem.Compute2DCoords(mol)

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    draw_options = drawer.drawOptions()
    draw_options.addStereoAnnotation = True
    draw_options.clearBackground = False

    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


@app.get("/")
def index():
    return send_from_directory(".", "index.html")


@app.get("/api/render")
def render_svg():
    smiles = request.args.get("smiles", "").strip()
    if not smiles:
        return jsonify({"error": "Parameteren 'smiles' mangler."}), 400

    try:
        svg = smiles_to_svg(smiles)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Kunne ikke generere struktur."}), 500

    return app.response_class(svg, mimetype="image/svg+xml")


@app.get("/api/download")
def download_svg():
    smiles = request.args.get("smiles", "").strip()
    if not smiles:
        return jsonify({"error": "Parameteren 'smiles' mangler."}), 400

    try:
        svg = smiles_to_svg(smiles)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Kunne ikke generere struktur."}), 500

    buffer = BytesIO(svg.encode("utf-8"))
    filename = "".join(ch if ch.isalnum() else "-" for ch in smiles.lower()).strip("-")[:60]
    if not filename:
        filename = "molecule"

    return send_file(
        buffer,
        mimetype="image/svg+xml",
        as_attachment=True,
        download_name=f"{filename}.svg",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
