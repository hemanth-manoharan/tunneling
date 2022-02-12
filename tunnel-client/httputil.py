import base64


def _is_chunked(headers):
    return headers.get("transfer-encoding") == "chunked"


def _get_headers_dict(headers):
    normal_dict = {}

    # TODO Handle for duplicates
    for key in headers.keys():
        # Do not relay transfer-encoding header as it is a per hop header
        if key.lower() == "transfer-encoding":
            continue
        # TODO Relaying the content-encoding header is causing issues.
        # for javascript files. To be investigated.
        if key.lower() == "content-encoding":
            continue
        normal_dict[key] = headers[key]
    return normal_dict


async def get_resp_body_str(http_response, logging):
    """
    Extracts the http response body as a base64 encoded string
    """

    if _is_chunked(http_response.headers):
        buffer = b""
        async for data, _ in http_response.content.iter_chunks():
            buffer += data
            resp_body = base64.b64encode(buffer).decode('utf-8')
    else:
        resp_body_bytes = await http_response.read()
        resp_body = base64.b64encode(resp_body_bytes).decode('utf-8')
    return resp_body


async def extract_resp_details(http_response, logging):
    """
    Extracts the http response header and body details
    """

    logging.info("Response status: %s", str(http_response.status))
    logging.debug("Response headers: %s", str(http_response.headers))
    resp_status = str(http_response.status)
    resp_headers = _get_headers_dict(http_response.headers)
    resp_body = await get_resp_body_str(http_response, logging)
    return resp_status, resp_headers, resp_body
