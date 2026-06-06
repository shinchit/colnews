from fetchers import Article


def test_article_dataclass():
    article = Article(
        source="Qiita",
        title="テスト記事",
        url="https://qiita.com/test",
        description="テスト説明",
    )
    assert article.source == "Qiita"
    assert article.title == "テスト記事"
    assert article.url == "https://qiita.com/test"
    assert article.description == "テスト説明"
