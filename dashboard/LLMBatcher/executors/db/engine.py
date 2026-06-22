from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker,async_scoped_session
import  asyncio
from sqlalchemy.orm import sessionmaker
import os

def create_engine_for_worker(worker_name: str):
    db_url = os.environ["DB_URL"]

    engine = create_engine(
        db_url,
        connect_args={
            "application_name": worker_name
        },
        pool_pre_ping=True
    )

    return engine


def create_sessionmaker(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)



def create_async_engine_for_worker(worker_name: str):
    db_url = os.environ["DB_URL"]

    db_url = db_url.replace("postgresql+psycopg2", "postgresql+asyncpg")

    engine = create_async_engine(
        db_url,
        # connect_args={
        #     "application_name": worker_name
        # },
        pool_pre_ping=True,
        # pool_size=20,
        # max_overflow=20,
    )

    return engine


def create_async_sessionmaker(engine):
    return async_sessionmaker(bind=engine, expire_on_commit=False)


def create_async_scoped_sessionmaker(session):
    return async_scoped_session(
        session, asyncio.current_task
    )


# engine = create_async_engine_for_worker(worker_name="test worker")
# session_local = create_async_sessionmaker(engine)

# async def single_call():
#     async with session_local() as session:
#         result = await session.execute(
#             select(Task)
#             .filter(Task.stage_name == Stages.end)
#             .with_for_update(skip_locked=True)
#             .limit(random.randint(1, 3))
#         )

#         tasks = result.scalars().all()
#         return len(tasks)

# async def test_call():
#     num_calls = 100
#     tasks = []

#     for i in range(num_calls):
#         tasks.append(single_call())

#     res = await asyncio.gather(*tasks)


#     for val in res:
#         print("Num. Sampled Tasks: ", val)

# asyncio.run(test_call())