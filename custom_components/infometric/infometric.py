from aiohttp import ClientSession
from dataclasses import dataclass


class InfometricException(Exception):
    pass


@dataclass
class InfometricMeter(object):
    id: str
    name: str
    label: str
    average: str
    prognosis: str
    last_values: list


class InfometricClient(object):
    url = None
    username = None
    password = None
    session: ClientSession = None

    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password

    async def authenticate(self, session):
        self.session = session
        try:
            resp = await self.session.post(
                url=self.url,
                data=f"UserName={self.username}&Password={self.password}&RememberMe=true&commit=Logga+in",
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
            return resp.ok
        except Exception as e:
            raise InfometricException(e)

    async def get_meters(self):
        ll = lambda x: {"series": x["SeriesId"], "time": x["Date"], "value": x["Value"]}
        try:
            resp = await self.session.post(
                url=f"{self.url}/Consumption/GetMeasureTypes"
            )
            return [
                InfometricMeter(
                    id=m["UnitId"],
                    label=m["UnitLabel"],
                    name=m["Name"],
                    average=m["AverageConsumption"],
                    prognosis=m["PrognosConsumption"],
                    last_values=[ll(x) for x in m["LastOKValues"]],
                )
                for m in await resp.json()
            ]
        except Exception as e:
            raise InfometricException(e)
