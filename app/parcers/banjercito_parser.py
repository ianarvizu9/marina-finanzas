import re
from datetime import datetime
from .base_parser import BaseParser

class BanjercitoParser(BaseParser):

    def parse(self, texto: str):
        movimientos = []

        # Ejemplo básico (lo ajustamos con tu PDF real)
        pattern = r"(\d{2}/\d{2}/\d{4})\s+(.*?)\s+(-?\d+\.\d{2})"

        matches = re.findall(pattern, texto)

        for match in matches:
            fecha_str, concepto, monto_str = match

            fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
            monto = float(monto_str)

            tipo = "ingreso" if monto > 0 else "egreso"

            movimientos.append({
                "numero_transaccion": "ABC123456",  # Aquí deberías extraer el número real del PDF
                "fecha": fecha,
                "concepto": concepto.strip(),
                "monto": abs(monto),
                "tipo": tipo,
                "banco": "Banjercito"
            })

        return movimientos