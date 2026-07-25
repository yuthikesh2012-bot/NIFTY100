class FeatureRepository:
    def __init__(self,session):
        self.session=session
    def save_features(self,features):
        self.session.append(features)
