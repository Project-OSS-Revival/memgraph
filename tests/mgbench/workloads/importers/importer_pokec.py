# Copyright 2023 Memgraph Ltd.
#
# Use of this software is governed by the Business Source License
# included in the file licenses/BSL.txt; by using this file, you agree to be bound by the terms of the Business Source
# License, and you may not use this file except in compliance with the Business Source License.
#
# As of the Change Date specified in that file, in accordance with
# the Business Source License, use of this software will be governed
# by the Apache License, Version 2.0, included in the file
# licenses/APL.txt.

from pathlib import Path

import log
from benchmark_context import BenchmarkContext
from constants import GraphVendors
from runners import BaseClient, BaseRunner
from workloads.importers.base import BaseImporter


class ImporterPokec(BaseImporter):
    def __init__(
        self,
        benchmark_context: BenchmarkContext,
        client: BaseClient,
        dataset_name: str,
        variant: str,
        index_file: str,
        dataset_file: str,
    ) -> None:
        super().__init__(benchmark_context, client)
        self._dataset_name = dataset_name
        self._variant = variant
        self._index_file = index_file
        self._dataset_file = dataset_file

    def execute_import(self):
        if self._benchmark_context.vendor_name == GraphVendors.NEO4J:
            neo4j_dump = Path() / ".cache" / "datasets" / self._dataset_name / self._variant / "neo4j.dump"
            vendor_runner = BaseRunner.create(
                benchmark_context=self._benchmark_context,
            )
            vendor_runner.clean_db()
            if neo4j_dump.exists():
                log.log("Loading database from existing dump...")
                vendor_runner.load_db_from_dump(path=neo4j_dump.parent)
            else:
                vendor_runner.start_db_init("import")
                print("Executing database index setup...")
                self._client.execute(file_path=self._index_file, num_workers=1)
                print("Importing dataset...")
                self._client.execute(
                    file_path=self._dataset_file, num_workers=self._benchmark_context.num_workers_for_import
                )
            return True
        elif self._benchmark_context.vendor_name == GraphVendors.POSTGRESQL:
            vendor_runner = BaseRunner.create(
                benchmark_context=self._benchmark_context,
            )
            vendor_runner.clean_db()
            vendor_runner.start_db_init("import")
            print("Executing database index setup...")
            self._client.execute(file_path=self._index_file, num_workers=1)
            print("Importing dataset...")
            self._client.execute(
                file_path=self._dataset_file, num_workers=self._benchmark_context.num_workers_for_import
            )
            vendor_runner.stop_db_init("import")
            return True
        else:
            return False
