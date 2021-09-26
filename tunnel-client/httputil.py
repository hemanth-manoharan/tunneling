import base64

bin_types = ["image/jpeg", "image/x-icon"]
def is_text(headers):
  if headers.get("content-type") in bin_types:
    return False
  else:
    return True

def get_headers_json(headers):
  # TODO Implement function correctly
  return {
    "content-type": headers["content-type"],
    "content-length": headers["content-length"]
  }

async def get_resp_body_str(httpResponse):
  is_text_resp = is_text(httpResponse.headers)
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
  resp_headers = get_headers_json(httpResponse.headers)
  resp_body = await get_resp_body_str(httpResponse)
  return resp_status, resp_headers, resp_body