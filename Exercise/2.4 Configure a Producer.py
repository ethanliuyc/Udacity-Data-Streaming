# Please complete the TODO items in the code.

import asyncio
from dataclasses import dataclass, field, astdict
import json
import random

from datetime import datetime
from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from faker import Faker


faker = Faker()

BROKER_URL = "PLAINTEXT://localhost:9092"
TOPIC_NAME = "org.udacity.exercise3.purchases"


@dataclass
class Purchase:
    username: str = field(default_factory=faker.user_name)
    currency: str = field(default_factory=faker.currency_code)
    amount: int = field(default_factory=lambda: random.randint(100, 200000))
    
    def serialize(self):
        """Serializes the object in JSON string format"""
        # Serializer the Purchase object
        # See: https://docs.python.org/3/library/json.html#json.dumps
        return json.dump(asdict(self))


async def produce_sync(topic_name):
    """Produces data synchronously into the Kafka Topic"""
    p = Producer({
        "bootstrap.servers": BROKER_URL，
        # linger time is the time interval for producer to group together any records that arrive in between request transmissions into a single batched request
        "linger.ms": "10000",
        # messages will be sent out as batch once it reach this batch number
        "batch.num.messages": "10000",
        # this number will never be hit since messages will be sent once accumulated to 10,000 
        "queue.buffering.max.messages" : "100000",
        "compression.type" : "lz4"
    })
    
    # TODO: Write a synchronous production loop.
    #       See: https://docs.confluent.io/current/clients/confluent-kafka-python/#confluent_kafka.Producer.flush
    while True:
        # TODO: Instantiate a `Purchase` on every iteration. Make sure to serialize it before
        #       sending it to Kafka!
        p.produce(topic_name, Purchase().serialize())
        if curr_iteration % 100000 == 0:
            elapsed = (datetime.utcnow()-start_time).seconds
            print(f"No. of message sent: {curr_iteration} | Total elapsed seconds: {elapsed}")
        curr_iteration += 1
        
        await asyncio.sleep(0.01)

        
def main():
    """Checks for topic and creates the topic if it does not exist"""
    create_topic(TOPIC_NAME)
    try:
        asyncio.run(produce_consume())
    except KeyboardInterrupt as e:
        print("shutting down")

    
async def produce_consume():
    """Runs the Producer and Consumer tasks"""
    t1 = asyncio.create_task(produce_sync(TOPIC_NAME))
    t2 = asyncio.create_task(_consume(TOPIC_NAME))
    await t1
    await t2

    
async def _consume(topic_name):
    """Consumes produced messages"""
    c = Consumer({"bootstrap.servers": BROKER_URL, "group.id": "0"})
    c.subscribe([topic_name])
    num_consumed=0
    while True:
        msg = c.consume(timeout=0.001)
        if msg:
            num_consumed += 1
            if num_consumed % 100 == 0:
                print(f"consumed {num_consumed} messages")
        else:
            await asyncio.sleep(0.01)

        
def create_topic(client):
    """Creates the topic with the given topic name"""
    client = AdminClient({"bootstrap.servers": BROKER_URL})
    futures = client.create_topics(
        [NewTopic(topic=TOPIC_NAME, num_partitions=5, replication_factor=1)]
    )
    for _, future in futures.items():
        try:
            future.result()
        except Exception as e:
            print("exiting production loop")


if __name__ == "__main__":
    main()