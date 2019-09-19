from cilantro_ee.protocol.transaction import transaction_is_valid
from cilantro_ee.storage.state import MetaDataStorage
from cilantro_ee.nodes.delegate.sub_block_builder import UnpackedContractTransaction
from cilantro_ee.messages import capnp as schemas
import os
import capnp
from contracting.stdlib.bridge.time import Datetime
from contracting.client import ContractingClient

from datetime import datetime
from . import conf

driver = MetaDataStorage()
client = ContractingClient()

transaction_capnp = capnp.load(os.path.dirname(schemas.__file__) + '/transaction.capnp')


def process_transaction(tx: transaction_capnp.Transaction):
    # Deserialize?

    if not transaction_is_valid(tx=tx,
                                expected_processor=conf.HOST_VK,
                                driver=driver,
                                strict=True):

        return {'error': 'Transaction is not valid.'}

    # Pass protocol level variables into environment so they are accessible at runtime in smart contracts
    block_hash = driver.latest_block_hash
    block_num = driver.latest_block_num

    dt = datetime.utcfromtimestamp(tx.metadata.timestamp)
    dt_object = Datetime(year=dt.year,
                         month=dt.month,
                         day=dt.day,
                         hour=dt.hour,
                         minute=dt.minute,
                         second=dt.second,
                         microsecond=dt.microsecond)

    environment = {
        'block_hash': block_hash,
        'block_num': block_num,
        'now': dt_object
    }

    transaction = UnpackedContractTransaction(tx)

    status_code, result, stamps_used = client.executor.execute(
        sender=transaction.payload.sender,
        contract_name=transaction.payload.contractName,
        function_name=transaction.payload.functionName,
        kwargs=transaction.payload.kwargs,
        stamps=transaction.payload.stampsSupplied,
        environment=environment,
        auto_commit=True
    )

    return {
        'status_code': status_code,
        'result': result,
        'stamps_used': stamps_used
    }