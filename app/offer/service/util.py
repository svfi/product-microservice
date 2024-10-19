import httpx
from loguru import logger
from sqlmodel import Session

from .db import read_token, update_token
from .model import AccessToken
from ...product.model import ProductPublic


def get_new_access_token(refresh_token: str, base_url: str) -> AccessToken | None:
    headers = {'Bearer': refresh_token}
    response = httpx.post(f'{base_url}/api/v1/auth', headers=headers)

    if response.status_code == 201:
        data = response.json()
        access_token_value = data['access_token']
        logger.info(f'New access token for offers is: {access_token_value}')
        return AccessToken(value=access_token_value)
    else:
        logger.error(f'Failed to obtain new access token for offers, reason: {response.text}')
        return None


def _request(refresh_token: str, base_url: str, session: Session, retries=3, **kwargs) -> httpx.Response:
    for _ in range(retries):
        # read access token from database
        access_token = read_token(session)
        if access_token:
            access_token_value = access_token.value
            logger.info(f'Loaded access token for offers is: {access_token_value}')
        else:
            new_access_token = get_new_access_token(refresh_token, base_url)
            if new_access_token:
                update_token(new_access_token, session)
                access_token_value = new_access_token.value
            else:
                continue

        # send request
        headers = {'Bearer': access_token_value}
        response = httpx.request(**kwargs, headers=headers)

        # check the use of invalid access token
        if response.status_code == 401:
            logger.error(f'Used access token was invalid: {access_token_value}')
            new_access_token = get_new_access_token(refresh_token, base_url)
            if new_access_token:
                update_token(new_access_token, session)
        else:
            return response

    raise RuntimeError('Failed to send request due to several invalid access tokens')


def register_product(product: ProductPublic, refresh_token: str, base_url: str, session: Session) -> httpx.Response:
    data = product.model_dump_json()
    logger.info(f'Register product with data: {data}')
    response = _request(refresh_token, base_url, session, method='POST',
                        url=f'{base_url}/api/v1/products/register', json=data)
    return response
