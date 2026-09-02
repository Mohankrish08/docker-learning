"""Task queue app — the SAME package runs as an API or as a worker.

Class 4 changes what lives BEHIND them: state moved out of a shared file
and into two real services, Postgres and Redis.
"""
