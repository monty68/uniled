"""Magic Hue Cloud Connect API"""
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from typing import Dict, Any, Final
import binascii
import requests
import hashlib
import urllib
import json
import time
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

MAGICHUE_COUNTRY_SERVERS: Final = [
    {
        "nationName": "Australia",
        "nationCode": "AU",
        "serverApi": "oameshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "oa.meshbroker.magichue.net",
    },
    {
        "nationName": "Avalon",
        "nationCode": "AL",
        "serverApi": "ttmeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "tt.meshbroker.magichue.net",
    },
    {
        "nationName": "China",
        "nationCode": "CN",
        "serverApi": "cnmeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "cn.meshbroker.magichue.net",
    },
    {
        "nationName": "United Kingdom",
        "nationCode": "GB",
        "serverApi": "eumeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "eu.meshbroker.magichue.net",
    },
    {
        "nationName": "Spain",
        "nationCode": "ES",
        "serverApi": "eumeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "eu.meshbroker.magichue.net",
    },
    {
        "nationName": "France",
        "nationCode": "FR",
        "serverApi": "eumeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "eu.meshbroker.magichue.net",
    },
    {
        "nationName": "Germany",
        "nationCode": "DE",
        "serverApi": "eumeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "eu.meshbroker.magichue.net",
    },
    {
        "nationName": "Italy",
        "nationCode": "IT",
        "serverApi": "eumeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "eu.meshbroker.magichue.net",
    },
    {
        "nationName": "Japan",
        "nationCode": "JP",
        "serverApi": "dymeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "dy.meshbroker.magichue.net",
    },
    {
        "nationName": "Russia",
        "nationCode": "RU",
        "serverApi": "eumeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "eu.meshbroker.magichue.net",
    },
    {
        "nationName": "United States",
        "nationCode": "US",
        "serverApi": "usmeshcloud.magichue.net:8081/MeshClouds/",
        "brokerApi": "us.meshbroker.magichue.net",
    },
]

MAGICHUE_RPC_NATION_DATA: Final = "apixp/MeshData/loadNationDataNew/ZG?language=en"
MAGICHUE_RPC_USER_LOGIN: Final = "apixp/User001/LoginForUser/ZG"
MAGICHUE_RPC_GET_MESH: Final = "apixp/MeshData/GetMyMeshPlaceItems/ZG?userId="
MAGICHUE_RPC_GET_MESH_DEVICES: Final = (
    "apixp/MeshData/GetMyMeshDeviceItems/ZG?placeUniID=&userId="
)

MAGICHUE_DEFAULT_COUNTRY: Final = "US"

class MagicHue:
    """Magic Hue Cloud Connector"""
    _country: str = None

    def __init__(self, username: str, password: str, country: str = MAGICHUE_DEFAULT_COUNTRY):
        """Initialize cloud connector"""
        self._server = "<unknown>"
        self._connect_url = None
        self._user_id = None
        self._auth_token = None
        self._device_secret = None
        self._mesh_data = None
        self._last_error = None
        self._username = username
        self._password = password
        self._country = self._country_code(country.upper())
        self._md5password = hashlib.md5(password.encode()).hexdigest()

    @staticmethod
    def dict_hash(dictionary: Dict[str, Any]) -> str:
        """MD5 hash of a dictionary."""
        dhash = hashlib.md5()
        encoded = json.dumps(dictionary, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()

    @staticmethod
    def countries():
        """Return list of supported country codes"""
        countries = list()
        for item in MAGICHUE_COUNTRY_SERVERS:
            countries.append((item["nationCode"], item["nationName"]))
        return countries

    @property
    def country(self) -> str:
        """Retun last operations result"""
        return self._country

    @property
    def last_error(self) -> str:
        """Retun last operations result"""
        return self._last_error

    @property
    def locations(self) -> list:
        """Return location list"""
        locations = list()
        for item in self.meshes:
            locations.append((item["placeUniID"], item["displayName"]))
        return locations

    @property
    def meshes(self) -> dict:
        """Return cached mesh data"""
        return self._mesh_data

    async def get_meshes(self) -> bool:
        """Get mesh data from MagicHue cloud server"""
        if self._mesh_data is not None and len(self._mesh_data):
            return self._mesh_data
        if self._auth_token:
            _LOGGER.info("MagicHue: Get meshes for: '%s'", self._user_id)
            self._last_error = None
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._connect_url
                    + MAGICHUE_RPC_GET_MESH
                    + urllib.parse.quote_plus(self._user_id),
                    headers=self._headers(),
                ) as response:
                    if response.status == 200:
                        response_json = await response.json()
                        _LOGGER.debug("MagicHue: Server mesh response: " + repr(response_json))
                        if response_json["ok"] == True:
                            self._mesh_data = response_json["result"]
                        else:
                            self._last_error = f"Get mesh failed: No result!"
                    else:
                        self._last_error = (
                            f"Get mesh failed, status code: {response.status}"
                        )
            if not self._last_error and self._mesh_data:
                for mesh in self._mesh_data:
                    mesh["deviceList"] = []
                    mesh["bridge"] = None
                    _LOGGER.info("MagicHue: Get bridge for: '%s'", mesh["displayName"])
                    if await self._get_bridge(mesh["placeUniID"]):
                        mesh.update({"bridge": self._bridge_data})
                return True
        else:
            self._last_error = "Get mesh failed, not logged in to cloud server!"
        _LOGGER.error(f"MagicHue: {self.last_error}")
        return False

    async def get_devices(self) -> bool:
        """Get mesh devices from MagicHue cloud server"""
        if self._auth_token:
            for mesh in self._mesh_data:
                placeUniID = mesh["placeUniID"]

                _LOGGER.info("MagicHue: Get devices for: '%s' (%s)", mesh["displayName"], placeUniID)
                endpoint = MAGICHUE_RPC_GET_MESH_DEVICES.replace(
                    "placeUniID=", "placeUniID=" + placeUniID
                )
                endpoint = endpoint.replace(
                    "userId=", "userId=" + urllib.parse.quote_plus(self._user_id)
                )
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self._connect_url + endpoint, headers=self._headers()
                    ) as response:
                        if response.status == 200:
                            response_json = await response.json()
                            _LOGGER.debug(
                                "MagicHue: Server device response: " + repr(response_json)
                            )
                            
                            if response_json["ok"] == True:
                                result_json = response_json["result"]
                                mesh.update({"deviceList": result_json})
                            else:
                                self._last_error = f"Get mesh devices failed: No result!"
                        else:
                            self._last_error = (
                                "Get mesh devices failed for placeUniID: "
                                + placeUniID
                                + " - "
                                + response.json()["error"]
                            )
                            _LOGGER.warning(f"MagicHue: {self.last_error}")
            return True
        else:
            self._last_error = "Get mesh failed, not logged in to cloud server!"
        _LOGGER.error(f"MagicHue: {self.last_error}")
        return False

    async def _get_bridge(self, placeUniID: str) -> bool:
        """Get mesh bridge from MagicHue cloud server"""
        endpoint = "apixp/Mqtt/getMasterControlData/ZG?placeUniID="
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self._connect_url + endpoint + placeUniID, headers=self._headers()
            ) as response:
                if response.status == 200:
                    response_json = await response.json()
                    _LOGGER.debug(
                        "MagicHue: Server bridge response: " + repr(response_json)
                    )
                    
                    if response_json["ok"] == True:
                        result_json = response.json()["result"]
                        self._bridge_data = result_json
                        return True
                else:
                    self._last_error = (
                        "Get mesh bridge, falied for placeUniID: "
                        + placeUniID
                        + " - "
                        + response.json()["error"]
                    )
                    _LOGGER.warning(f"MagicHue: {self.last_error}")
        self._bridge_data = None
        return False

    async def login(self) -> bool:
        """Login in to MagicHue cloud server"""
        self._auth_token = ""
        timestampcheckcode = self._generate_timestamp_checkcode()
        timestamp = timestampcheckcode[0]
        checkcode = timestampcheckcode[1]
        payload = dict(
            userID=self._username,
            password=self._md5password,
            appSys="Android",
            timestamp=timestamp,
            appVer="",
            checkcode=checkcode,
        )
        _LOGGER.info("MagicHue: Server login: '%s'", self._server)
        if self._connect_url is not None:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._connect_url + MAGICHUE_RPC_USER_LOGIN,
                    headers=self._headers(),
                    json=payload,
                ) as response:
                    if response.status == 200:
                        response_json = await response.json()
                        _LOGGER.debug("MagicHue: Server login response: " + repr(response_json))
                        if response_json["ok"] == True:
                            result_json = response_json["result"]
                            self._user_id = result_json["userId"]
                            self._auth_token = result_json["auth_token"]
                            self._device_secret = result_json["deviceSecret"]
                            self._country = self._country_code(result_json["nationCode"])
                            self._last_error = None
                            return True
                        else:
                            self._last_error = "Login failed: " + response_json["err_msg"]
                    else:
                        self._last_error = f"Login failed, status code: {response.status}"
        else:
            self._last_error = f"Login failed, no valid cloud server identified."
        _LOGGER.error(f"MagicHue: {self.last_error}")
        return False

    def _headers(self) -> dict:
        """Default HTTP headers"""
        return {
            "User-Agent": "HaoDeng/1.5.7(ANDROID,10,en-US)",
            "Accept-Language": "en-US",
            "Accept": "application/json",
            "token": self._auth_token,
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip",
        }

    def _country_code(self, country: str) -> str:
        """Return country server URL"""
        if country and country != "" and country != self.country:
            self._server = self._country_server(country)
            self._connect_url = "http://" + self._server
            _LOGGER.debug("MagicHue: Server set to: " + country + " - " + self._server)
            return country
        return self.country

    def _country_server(self, country: str) -> str:
        """Return country server URL"""
        for item in MAGICHUE_COUNTRY_SERVERS:
            if item["nationCode"] == country:
                return item["serverApi"]
        # return US server by default
        return MAGICHUE_COUNTRY_SERVERS[10]["serverApi"]

    def _generate_timestamp_checkcode(self):
        """Generate timestamo and check code"""
        SECRET_KEY = "0FC154F9C01DFA9656524A0EFABC994F"
        timestamp = str(int(time.time() * 1000))
        value = ("ZG" + timestamp).encode()
        backend = default_backend()
        key = (SECRET_KEY).encode()
        encryptor = Cipher(algorithms.AES(key), modes.ECB(), backend).encryptor()
        padder = padding.PKCS7(algorithms.AES(key).block_size).padder()
        padded_data = padder.update(value) + padder.finalize()
        encrypted_text = encryptor.update(padded_data) + encryptor.finalize()
        checkcode = binascii.hexlify(encrypted_text).decode()
        return timestamp, checkcode
