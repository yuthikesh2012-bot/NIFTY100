class TransactionManager:
    def __init__(self,session): self.session=session
    def __enter__(self): return self.session
    def __exit__(self,exc_type,exc,tb):
        if exc: self.session.rollback()
        else: self.session.commit()
