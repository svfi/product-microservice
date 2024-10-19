from sqlmodel import select, Session

from .model import AccessToken


def read_token(session: Session) -> AccessToken | None:
    return session.exec(select(AccessToken)).first()


def update_token(token: AccessToken, session: Session):
    db_token = read_token(session)

    if db_token:
        token_data = token.model_dump(exclude_unset=True)
        db_token.sqlmodel_update(token_data)
    else:
        db_token = token

    session.add(db_token)
    session.commit()
