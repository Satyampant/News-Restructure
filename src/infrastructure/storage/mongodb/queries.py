# Complex query builders
def build_sentiment_aggregation_pipeline() -> list:
    """Build aggregation pipeline for sentiment statistics."""
    return [
        {
            "$match": {
                "sentiment": {"$ne": None}
            }
        },
        {
            "$group": {
                "_id": "$sentiment.classification",
                "count": {"$sum": 1},
                "avg_confidence": {"$avg": "$sentiment.confidence_score"}
            }
        }
    ]

def build_supply_chain_aggregation_pipeline() -> list:
    """Build aggregation pipeline for supply chain statistics."""
    return [
        {
            "$match": {
                "cross_impacts": {"$exists": True, "$ne": []}
            }
        },
        {
            "$project": {
                "id": 1,
                "cross_impacts": 1,
                "impact_count": {"$size": "$cross_impacts"}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_articles": {"$sum": 1},
                "total_impacts": {"$sum": "$impact_count"},
                "max_impacts": {"$max": "$impact_count"},
                "avg_impacts": {"$avg": "$impact_count"}
            }
        }
    ]