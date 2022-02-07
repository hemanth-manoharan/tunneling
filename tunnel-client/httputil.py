import base64

bin_types = ["image/jpeg", "image/x-icon", "image/png"]

def is_text(headers):
  if headers.get("content-type") in bin_types:
    return False
  else:
    return True

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

async def get_resp_body_str(httpResponse, logging):
  is_text_resp = is_text(httpResponse.headers)

  if _is_chunked(httpResponse.headers):
    buffer = b""
    async for data, _ in httpResponse.content.iter_chunks():
      buffer += data
    if is_text_resp:
      resp_body = buffer.decode("utf-8")
    else:
      resp_body = base64.b64encode(buffer).decode('utf-8')
  else:
    if is_text_resp:
      resp_body = await httpResponse.text()
    else:
      resp_body_bytes = await httpResponse.read()
      resp_body = base64.b64encode(resp_body_bytes).decode('utf-8')
  return resp_body

async def extract_response_details(httpResponse, logging):
  logging.info("Response status: " + str(httpResponse.status))
  logging.debug("Response headers: " + str(httpResponse.headers))
  resp_status = str(httpResponse.status)
  resp_headers = _get_headers_dict(httpResponse.headers)
  resp_body = await get_resp_body_str(httpResponse, logging)
  return resp_status, resp_headers, resp_body