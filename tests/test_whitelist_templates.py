from app.core.whitelist_templates import WhitelistTemplateStore


def test_whitelist_templates_roundtrip(tmp_path):
    path = tmp_path / 'templates.json'
    store = WhitelistTemplateStore(path)

    assert store.list_templates() == []

    store.upsert_template(
        name='写作',
        allowed_process_names=['CODE.EXE', 'code.exe', 'chrome.exe'],
        allowed_title_keywords=['Notion', '论文', 'Notion'],
    )

    tpl = store.get_template('写作')
    assert tpl is not None
    assert tpl.allowed_process_names == ['chrome.exe', 'code.exe']
    assert tpl.allowed_title_keywords == ['Notion', '论文']

    assert store.has_template('写作') is True

    store.delete_template('写作')
    assert store.get_template('写作') is None
    assert store.list_templates() == []
