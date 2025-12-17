#!/usr/bin/env python3
"""
Script to automatically create the MarketMuni project directory structure.
Run this script to generate the complete folder hierarchy with all necessary files.

Usage:
    python create_project_structure.py [--base-dir <path>]
"""

import os
import argparse
from pathlib import Path
from typing import List, Dict


def create_directory_structure(base_path: Path) -> None:
    """
    Create the complete MarketMuni directory structure.
    
    Args:
        base_path: The base directory where the structure will be created
    """
    
    # Define the complete directory structure
    structure = {
        "marketmuni": {
            "src": {
                "domain": {
                    "__init__.py": "",
                    "models": {
                        "__init__.py": "",
                        "article.py": "# NewsArticle + domain methods\n",
                        "entities.py": "# Entity extraction models\n",
                        "sentiment.py": "# Sentiment models\n",
                        "stock_impact.py": "# Stock impact models\n",
                        "supply_chain.py": "# Supply chain models\n",
                        "query.py": "# Query routing models\n",
                    },
                    "services": {
                        "__init__.py": "",
                        "entity_normalization.py": "# Fuzzy matching, validation\n",
                        "sentiment_scoring.py": "# Sentiment calculation logic\n",
                        "impact_scoring.py": "# Stock impact scoring\n",
                        "deduplication_logic.py": "# Similarity algorithms\n",
                    },
                    "events": {
                        "__init__.py": "",
                        "article_events.py": "",
                    },
                },
                "application": {
                    "__init__.py": "",
                    "workflows": {
                        "__init__.py": "",
                        "ingestion_graph.py": "# Graph structure + edges\n",
                        "query_graph.py": "# Graph structure + edges\n",
                        "state.py": "# TypedDict state definitions\n",
                    },
                    "nodes": {
                        "__init__.py": "",
                        "ingestion": {
                            "__init__.py": "",
                            "ingestion_node.py": "",
                            "deduplication_node.py": "",
                            "entity_extraction_node.py": "",
                            "impact_mapping_node.py": "",
                            "sentiment_analysis_node.py": "",
                            "supply_chain_node.py": "",
                            "indexing_node.py": "",
                        },
                        "query": {
                            "__init__.py": "",
                            "query_node.py": "",
                        },
                    },
                    "agents": {
                        "__init__.py": "",
                        "base.py": "# Base agent interface\n",
                        "entity_agent.py": "# Calls LLM + domain logic\n",
                        "sentiment_agent.py": "",
                        "stock_impact_agent.py": "",
                        "supply_chain_agent.py": "",
                        "query_router_agent.py": "",
                        "deduplication_agent.py": "",
                    },
                    "use_cases": {
                        "__init__.py": "",
                        "process_article.py": "",
                        "execute_query.py": "",
                    },
                },
                "infrastructure": {
                    "__init__.py": "",
                    "llm": {
                        "__init__.py": "",
                        "base.py": "# Abstract LLM interface\n",
                        "groq_client.py": "# Groq implementation\n",
                        "prompt_builder.py": "# Prompt construction utilities\n",
                    },
                    "storage": {
                        "__init__.py": "",
                        "mongodb": {
                            "__init__.py": "",
                            "client.py": "# MongoDB connection\n",
                            "article_repository.py": "",
                            "queries.py": "# Complex query builders\n",
                        },
                        "vector": {
                            "__init__.py": "",
                            "chroma_client.py": "",
                            "embeddings.py": "",
                        },
                        "cache": {
                            "__init__.py": "",
                            "redis_cache.py": "",
                        },
                    },
                    "external": {
                        "__init__.py": "",
                        "news_feeds.py": "# Future news API integrations\n",
                    },
                },
                "configuration": {
                    "__init__.py": "",
                    "settings.py": "# Pydantic Settings from config.yaml\n",
                    "prompts": {
                        "__init__.py": "",
                        "entity_extraction.yaml": "",
                        "sentiment_analysis.yaml": "",
                        "stock_impact.yaml": "",
                        "supply_chain.yaml": "",
                        "query_routing.yaml": "",
                    },
                    "schemas": {
                        "article_input.json": "",
                    },
                    "loader.py": "# Configuration loading logic\n",
                },
                "interfaces": {
                    "__init__.py": "",
                    "rest": {
                        "__init__.py": "",
                        "app.py": "# FastAPI app factory\n",
                        "routes": {
                            "__init__.py": "",
                            "ingestion.py": "",
                            "query.py": "",
                            "articles.py": "",
                            "health.py": "",
                            "stats.py": "",
                        },
                        "schemas": {
                            "__init__.py": "",
                            "requests.py": "",
                            "responses.py": "",
                        },
                        "dependencies.py": "# FastAPI dependency injection\n",
                    },
                    "cli": {
                        "__init__.py": "",
                    },
                },
                "shared": {
                    "__init__.py": "",
                    "types": {
                        "__init__.py": "",
                        "common.py": "",
                    },
                    "exceptions": {
                        "__init__.py": "",
                        "domain_exceptions.py": "",
                        "infrastructure_exceptions.py": "",
                        "validation_exceptions.py": "",
                    },
                    "utils": {
                        "__init__.py": "",
                        "text_processing.py": "",
                        "date_utils.py": "",
                        "validation.py": "",
                    },
                    "logging": {
                        "__init__.py": "",
                        "logger.py": "",
                    },
                },
                "__init__.py": "",
            },
            "tests": {
                "unit": {
                    "domain": {},
                    "application": {},
                    "infrastructure": {},
                },
                "integration": {
                    "workflows": {},
                    "agents": {},
                },
                "e2e": {
                    "test_complete_pipeline.py": "",
                },
                "fixtures": {
                    "mock_articles.json": "",
                    "llm_responses.json": "",
                },
                "conftest.py": "",
            },
            "scripts": {
                "setup_indexes.py": "",
                "migrate_data.py": "",
                "seed_test_data.py": "",
            },
            "docs": {
                "architecture": {
                    "adr": {},
                    "diagrams": {},
                    "component_interactions.md": "",
                },
                "api": {
                    "openapi.yaml": "",
                },
            },
            "config": {
                "development.yaml": "",
                "production.yaml": "",
                "test.yaml": "",
            },
            "run.py": "# Application entry point\n",
            "pyproject.toml": "",
            "pytest.ini": "",
            "README.md": "# MarketMuni\n\nFinancial news analysis and stock impact prediction system.\n",
        }
    }
    
    def create_structure(current_path: Path, structure_dict: Dict) -> None:
        """
        Recursively create directories and files from the structure dictionary.
        
        Args:
            current_path: Current directory path
            structure_dict: Dictionary representing the structure
        """
        for name, content in structure_dict.items():
            item_path = current_path / name
            
            if isinstance(content, dict):
                # It's a directory
                item_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {item_path}")
                create_structure(item_path, content)
            else:
                # It's a file
                item_path.parent.mkdir(parents=True, exist_ok=True)
                with open(item_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Created file: {item_path}")
    
    # Create the structure
    print(f"Creating MarketMuni project structure at: {base_path}")
    print("=" * 80)
    create_structure(base_path, structure)
    print("=" * 80)
    print(f"✓ Project structure created successfully at: {base_path / 'marketmuni'}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Create the MarketMuni project directory structure"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory where the structure will be created (default: current directory)"
    )
    
    args = parser.parse_args()
    base_path = Path(args.base_dir).resolve()
    
    # Confirm creation
    print(f"\nThis will create the MarketMuni project structure in: {base_path}")
    response = input("Do you want to continue? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        create_directory_structure(base_path)
        print("\n✓ Done! Your project structure is ready.")
        print(f"\nTo get started:")
        print(f"  cd {base_path / 'marketmuni'}")
        print(f"  # Start developing your application")
    else:
        print("Operation cancelled.")


if __name__ == "__main__":
    main()
