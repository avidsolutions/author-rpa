"""Database operations module for RPA framework."""

from typing import Any, Dict, List, Optional, Type, Union
from contextlib import contextmanager

from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from ..core.logger import LoggerMixin


class DatabaseModule(LoggerMixin):
    """Handle database operations using SQLAlchemy."""

    def __init__(self, connection_string: Optional[str] = None):
        self._engine: Optional[Engine] = None
        self._session_factory = None
        self._metadata = MetaData()

        if connection_string:
            self.connect(connection_string)

    def connect(self, connection_string: str) -> None:
        """Connect to a database.

        Args:
            connection_string: SQLAlchemy connection string
                Examples:
                - sqlite:///data.db
                - postgresql://user:pass@localhost/dbname
                - mysql://user:pass@localhost/dbname
        """
        self._engine = create_engine(connection_string)
        self._session_factory = sessionmaker(bind=self._engine)
        self.logger.info(f"Connected to database: {connection_string.split('@')[-1]}")

    @contextmanager
    def session(self):
        """Create a database session context manager."""
        if not self._session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows as dicts
        """
        with self.session() as session:
            result = session.execute(text(query), params or {})

            if result.returns_rows:
                rows = [dict(row._mapping) for row in result]
                self.logger.info(f"Query returned {len(rows)} rows")
                return rows
            else:
                self.logger.info(f"Query affected {result.rowcount} rows")
                return []

    def query(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query a table with simple conditions.

        Args:
            table: Table name
            columns: Columns to select (default: all)
            where: Dict of column=value conditions (AND)
            order_by: Column to order by
            limit: Maximum rows to return

        Returns:
            List of rows as dicts
        """
        cols = ", ".join(columns) if columns else "*"
        query = f"SELECT {cols} FROM {table}"

        params = {}
        if where:
            conditions = []
            for i, (col, val) in enumerate(where.items()):
                param_name = f"p{i}"
                conditions.append(f"{col} = :{param_name}")
                params[param_name] = val
            query += " WHERE " + " AND ".join(conditions)

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        return self.execute(query, params)

    def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> int:
        """Insert data into a table.

        Args:
            table: Table name
            data: Dict or list of dicts to insert

        Returns:
            Number of rows inserted
        """
        if isinstance(data, dict):
            data = [data]

        if not data:
            return 0

        columns = list(data[0].keys())
        col_str = ", ".join(columns)
        val_str = ", ".join(f":{col}" for col in columns)

        query = f"INSERT INTO {table} ({col_str}) VALUES ({val_str})"

        count = 0
        with self.session() as session:
            for row in data:
                session.execute(text(query), row)
                count += 1

        self.logger.info(f"Inserted {count} rows into {table}")
        return count

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any],
    ) -> int:
        """Update rows in a table.

        Args:
            table: Table name
            data: Dict of column=value to update
            where: Dict of conditions

        Returns:
            Number of rows updated
        """
        set_parts = []
        params = {}

        for i, (col, val) in enumerate(data.items()):
            param_name = f"s{i}"
            set_parts.append(f"{col} = :{param_name}")
            params[param_name] = val

        where_parts = []
        for i, (col, val) in enumerate(where.items()):
            param_name = f"w{i}"
            where_parts.append(f"{col} = :{param_name}")
            params[param_name] = val

        query = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"

        with self.session() as session:
            result = session.execute(text(query), params)
            count = result.rowcount

        self.logger.info(f"Updated {count} rows in {table}")
        return count

    def delete(
        self,
        table: str,
        where: Dict[str, Any],
    ) -> int:
        """Delete rows from a table.

        Args:
            table: Table name
            where: Dict of conditions

        Returns:
            Number of rows deleted
        """
        parts = []
        params = {}

        for i, (col, val) in enumerate(where.items()):
            param_name = f"p{i}"
            parts.append(f"{col} = :{param_name}")
            params[param_name] = val

        query = f"DELETE FROM {table} WHERE {' AND '.join(parts)}"

        with self.session() as session:
            result = session.execute(text(query), params)
            count = result.rowcount

        self.logger.info(f"Deleted {count} rows from {table}")
        return count

    def create_table(
        self,
        table: str,
        columns: Dict[str, str],
        primary_key: Optional[str] = None,
    ) -> None:
        """Create a new table.

        Args:
            table: Table name
            columns: Dict of column_name: type_definition
            primary_key: Primary key column
        """
        col_defs = []
        for col, typedef in columns.items():
            if col == primary_key:
                col_defs.append(f"{col} {typedef} PRIMARY KEY")
            else:
                col_defs.append(f"{col} {typedef}")

        query = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(col_defs)})"

        with self.session() as session:
            session.execute(text(query))

        self.logger.info(f"Created table: {table}")

    def drop_table(self, table: str) -> None:
        """Drop a table."""
        with self.session() as session:
            session.execute(text(f"DROP TABLE IF EXISTS {table}"))
        self.logger.info(f"Dropped table: {table}")

    def table_exists(self, table: str) -> bool:
        """Check if a table exists."""
        inspector = inspect(self._engine)
        return table in inspector.get_table_names()

    def get_tables(self) -> List[str]:
        """Get list of all tables."""
        inspector = inspect(self._engine)
        return inspector.get_table_names()

    def get_columns(self, table: str) -> List[Dict[str, Any]]:
        """Get column information for a table."""
        inspector = inspect(self._engine)
        return [dict(col) for col in inspector.get_columns(table)]

    def count(self, table: str, where: Optional[Dict[str, Any]] = None) -> int:
        """Count rows in a table."""
        query = f"SELECT COUNT(*) as cnt FROM {table}"
        params = {}

        if where:
            parts = []
            for i, (col, val) in enumerate(where.items()):
                param_name = f"p{i}"
                parts.append(f"{col} = :{param_name}")
                params[param_name] = val
            query += " WHERE " + " AND ".join(parts)

        result = self.execute(query, params)
        return result[0]["cnt"] if result else 0

    def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        key_columns: List[str],
    ) -> None:
        """Insert or update a row.

        Args:
            table: Table name
            data: Row data
            key_columns: Columns to match for update
        """
        where = {col: data[col] for col in key_columns}
        existing = self.query(table, where=where, limit=1)

        if existing:
            update_data = {k: v for k, v in data.items() if k not in key_columns}
            if update_data:
                self.update(table, update_data, where)
        else:
            self.insert(table, data)

    def bulk_insert(
        self,
        table: str,
        data: List[Dict[str, Any]],
        batch_size: int = 1000,
    ) -> int:
        """Insert many rows efficiently.

        Args:
            table: Table name
            data: List of rows
            batch_size: Rows per batch

        Returns:
            Total rows inserted
        """
        total = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            total += self.insert(table, batch)

        return total

    def transaction(self):
        """Get a transaction context manager."""
        return self.session()

    def close(self) -> None:
        """Close database connection."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self.logger.info("Database connection closed")
