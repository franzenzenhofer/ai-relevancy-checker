"""Google Search Console API client."""
import json
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from .config import config
from .gsc_query import QueryRecord, parse_gsc_response


class GSCClient:
    """GSC API client with token refresh."""

    def __init__(self) -> None:
        self.creds: Optional[Credentials] = None
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        if not config.token_path.exists():
            raise FileNotFoundError(f"Token not found: {config.token_path}")
        token_data = json.loads(config.token_path.read_text())
        self.creds = Credentials(
            token=token_data.get("token"), refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"), client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes", config.gsc_scopes),
        )
        if self.creds.expired or not self.creds.valid:
            print("Refreshing GSC token...")
            self.creds.refresh(Request())
            self._save_token()
        self.service = build("webmasters", "v3", credentials=self.creds)
        print("GSC API authenticated successfully")

    def _save_token(self) -> None:
        token_data = {
            "token": self.creds.token, "refresh_token": self.creds.refresh_token,
            "token_uri": self.creds.token_uri, "client_id": self.creds.client_id,
            "client_secret": self.creds.client_secret,
            "scopes": list(self.creds.scopes) if self.creds.scopes else [],
            "expiry": self.creds.expiry.isoformat() if self.creds.expiry else None,
        }
        config.token_path.write_text(json.dumps(token_data, indent=2))

    def get_top_queries(
        self, site_url: str, start_date: str, end_date: str, max_queries: int = 100
    ) -> List[QueryRecord]:
        # Fetch max rows based on config - no hidden defaults
        row_limit = config.gsc_row_limit
        body: Dict = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": config.gsc_dimensions,
            "rowLimit": row_limit,
        }
        response = self.service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        rows = response.get("rows", [])
        print(f"GSC returned {len(rows)} rows (fetched max {row_limit})")
        return parse_gsc_response(rows, max_queries)
