import logging
import requests
from pathlib import Path
from base64 import b64encode
from robot.api.deco import keyword

# Configurar el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoLibrary:
    def __init__(self, organization_url, personal_access_token):
        self.organization_url = organization_url
        self.personal_access_token = personal_access_token
        self.headers = {
            "Content-Type": "application/json-patch+json",
            "Authorization": f"Basic {self._encode_pat()}"
        }

    def _encode_pat(self):
        pat = f":{self.personal_access_token}".encode("utf-8")
        return b64encode(pat).decode("utf-8")

    @keyword("Update Work Item State")
    def update_work_item_state(self, project, work_item_id, new_state, new_description, new_test_cycle):
        url = f"{self.organization_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=6.0"
        data = [
            {"op": "add", "path": "/fields/System.State", "value": new_state},
            {"op": "add", "path": "/fields/System.Description", "value": new_description},
            {"op": "add", "path": "/fields/Custom.CiclodePruebas", "value": new_test_cycle}
        ]

        logger.info(f"Realizando petición PATCH a: {url}")
        response = requests.patch(url, json=data, headers=self.headers)
        logger.info(f"Código de estado de la respuesta: {response.status_code}")
        response.raise_for_status()
        return response.json()

    @keyword("Add Screenshot to Work Item Comment If Failed")
    def add_screenshot_to_work_item_comment_if_failed(self, project, work_item_id, screenshot_path, test_status):
        if test_status == "FAIL":
            # Subir la imagen como un adjunto
            with open(screenshot_path, "rb") as f:
                screenshot_data = f.read()

            attachment_url = f"{self.organization_url}/{project}/_apis/wit/attachments?fileName={screenshot_path}&api-version=6.0"
            headers = {
                "Content-Type": "application/octet-stream",
                "Authorization": f"Basic {self._encode_pat()}"
            }

            logger.info(f"Subiendo captura de pantalla como adjunto: {screenshot_path}")
            attachment_response = requests.post(attachment_url, headers=headers, data=screenshot_data)
            attachment_response.raise_for_status()
            attachment_id = attachment_response.json()["url"]

            # Agregar el enlace de la imagen al comentario en formato de hipervínculo
            work_item_url = f"{self.organization_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=6.0"
            data = [
                {
                    "op": "add",
                    "path": "/fields/System.History",
                    "value": f"<div>Evidencia: <a href=\"{attachment_id}\">{attachment_id}</a></div>"
                }
            ]

            logger.info(f"Agregando comentario con enlace a la captura de pantalla al work item en: {work_item_url}")
            response = requests.patch(work_item_url, json=data, headers=self.headers)
            response.raise_for_status()
            logger.info(f"Código de estado de la respuesta: {response.status_code}")
            return response.json()

    @keyword("Get Latest Screenshot Path")
    def get_latest_screenshot_path(self, directory, pattern="selenium-screenshot-"):
        # Asegurarse de que el directorio sea de tipo Path
        directory_path = Path(directory)

        # Buscar archivos que empiecen con el patrón y terminen en .png
        files = [f for f in directory_path.iterdir() if f.name.startswith(pattern) and f.suffix == ".png"]
        if not files:
            raise FileNotFoundError("No screenshots found matching the pattern.")
        
        # Ordenar archivos por fecha de modificación y obtener el más reciente
        files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
        latest_screenshot_path = files[0]

        # Convertir a cadena antes de devolver
        return str(latest_screenshot_path)
