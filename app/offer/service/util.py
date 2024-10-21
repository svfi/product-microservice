"""Utility functions to support interaction with the 3rd party offer microservice."""

from uuid import UUID

import httpx
from loguru import logger
from sqlmodel import Session

from .db import read_token, update_token
from .model import AccessToken
from ..model import OfferPublic
from ...product.db import read_products, update_product_offers
from ...product.model import ProductPublic


AUTH_ENDPOINT = '/api/v1/auth'
REGISTER_PRODUCT_ENDPOINT = '/api/v1/products/register'


def _renew_access_token(refresh_token: str, base_url: str) -> AccessToken | None:
    headers = {'Bearer': refresh_token}
    response = httpx.post(f'{base_url}{AUTH_ENDPOINT}', headers=headers)

    if response.status_code == 201:
        data = response.json()
        access_token_value = data['access_token']
        logger.info(f'New access token for offers is: {access_token_value}')
        return AccessToken(value=access_token_value)
    else:
        logger.error(f'Failed to obtain new access token for offers, reason: {response.text}')
        return None


def _send_request(refresh_token: str, base_url: str, session: Session, retries=3, **kwargs) -> httpx.Response:
    """
    Sends an HTTP request with a loaded/fetched up-to-date access token in the headers.

    :param refresh_token: refresh token used to generate the access token
    :param base_url: base url for access token generation
    :param session: database session
    :param retries: number of retries for how many times to try to send the request
    :keyword **kwargs: keyword arguments passed to `httpx.request` performing the actual request
    :return: httpx.Response
    :raises RuntimeError: if the action was not successful after all retries
    """

    for _ in range(retries):
        # read access token from database
        access_token = read_token(session)
        if access_token:
            access_token_value = access_token.value
            logger.info(f'Loaded access token for offers is: {access_token_value}')
        else:
            new_access_token = _renew_access_token(refresh_token, base_url)
            if new_access_token:
                update_token(new_access_token, session)
                access_token_value = new_access_token.value
            else:
                continue

        # send request
        headers = {'Bearer': access_token_value}
        response = httpx.request(**kwargs, headers=headers)

        # check the potential use of invalid access token
        if response.status_code == 401:
            logger.error(f'Used access token was invalid: {access_token_value}')
            new_access_token = _renew_access_token(refresh_token, base_url)
            if new_access_token:
                update_token(new_access_token, session)
        else:
            return response

    raise RuntimeError('Failed to send request due to several invalid access tokens')


def register_product(product: ProductPublic, refresh_token: str, base_url: str, session: Session) -> httpx.Response:
    data = product.model_dump(mode='json')
    logger.info(f'Register product with data: {data}')
    response = _send_request(refresh_token, base_url, session,
                             method='POST', url=f'{base_url}{REGISTER_PRODUCT_ENDPOINT}', json=data)

    if response.status_code != 201:
        logger.error(f'Failed to register product {product}, reason: {response.text}')

    return response


def _get_offers(product_id: UUID, refresh_token: str, base_url: str, session: Session) -> list[OfferPublic] | None:
    response = _send_request(refresh_token, base_url, session,
                             method='GET', url=f'{base_url}/api/v1/products/{product_id}/offers')

    if response.status_code == 200:
        data = response.json()
        offers = [OfferPublic.model_validate(item) for item in data]
        return offers

    logger.error(f'Failed to obtain new offers for product {product_id}, reason: {response.text}')
    return None


def update_all_products_offers(refresh_token: str, base_url: str, session: Session):
    products = read_products(session)
    logger.info(f'Updating offers for all ({len(products)}) products')

    for product in products:
        offers = _get_offers(product.id, refresh_token, base_url, session)
        if offers is not None:
            update_product_offers(product.id, offers, session)
