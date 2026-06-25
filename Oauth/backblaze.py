from dotenv import load_dotenv
import os

load_dotenv()
from b2sdk.v2 import InMemoryAccountInfo, B2Api


BACKBLAZE_ID = os.getenv("BACKBLAZE_KEYID")
BACKBLAZE_APPID = os.getenv("BACKBLAZE_APPLICATIONKEY")
BUCKET = os.getenv("BUCKET")


class _LazyBackblaze:
    def __init__(self):
        self._initialized = False
        self._bucket = None

    def _ensure(self):
        if self._initialized:
            return
        # Only initialize if all env vars are present
        if not BACKBLAZE_ID or not BACKBLAZE_APPID or not BUCKET:
            raise RuntimeError("Backblaze is not configured (missing env vars)")
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        # May raise if B2 is unavailable; let the caller handle in request scope
        b2_api.authorize_account(
            realm="production",
            application_key_id=BACKBLAZE_ID,
            application_key=BACKBLAZE_APPID,
        )
        self._bucket = b2_api.get_bucket_by_name(BUCKET)
        self._initialized = True

    def upload_file(self, file, path):
        self._ensure()
        file_version = self._bucket.upload_bytes(
            data_bytes=file.read(),
            file_name=path,
            content_type=getattr(file, "content_type", None) or "b2/x-auto",
        )
        return file_version.id_

    def get_url(self, file_id):
        self._ensure()
        file = self._bucket.get_file_info_by_id(file_id)
        authorization = self._bucket.get_download_authorization(
            file_name_prefix=file.file_name, valid_duration_in_seconds=3600
        )
        return f"{self._bucket.get_download_url(file.file_name)}?Authorization={authorization}"


# Keep the same symbol used elsewhere, but lazy
blaze_client = _LazyBackblaze()
