try:
    import requests
except ImportError:
    import urequests as requests

from .errors import NetworkError


def get_json(url, timeout_seconds=20):
    response = None
    try:
        try:
            response = requests.get(url, timeout=timeout_seconds)
        except TypeError:
            response = requests.get(url)

        if getattr(response, "status_code", 200) != 200:
            raise NetworkError(
                "HTTP %s while requesting %s"
                % (getattr(response, "status_code", "?"), url)
            )
        return response.json()
    except NetworkError:
        raise
    except Exception as exc:
        raise NetworkError("Failed to download JSON: %s" % exc)
    finally:
        if response is not None:
            response.close()


def download_to_file(url, destination, hasher, chunk_size=1024, timeout_seconds=20):
    response = None
    bytes_written = 0

    try:
        try:
            response = requests.get(url, stream=True, timeout=timeout_seconds)
        except TypeError:
            response = requests.get(url, stream=True)

        if getattr(response, "status_code", 200) != 200:
            raise NetworkError(
                "HTTP %s while downloading %s"
                % (getattr(response, "status_code", "?"), url)
            )

        with open(destination, "wb") as target:
            raw = getattr(response, "raw", None)
            if raw is None:
                data = response.content
                target.write(data)
                hasher.update(data)
                return len(data)

            while True:
                chunk = raw.read(chunk_size)
                if not chunk:
                    break
                target.write(chunk)
                hasher.update(chunk)
                bytes_written += len(chunk)

        return bytes_written
    except NetworkError:
        raise
    except Exception as exc:
        raise NetworkError("Failed to download %s: %s" % (url, exc))
    finally:
        if response is not None:
            response.close()
