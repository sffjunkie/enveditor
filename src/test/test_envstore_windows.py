from enveditor.envstore import WindowsEnvStore

def test_WindowsEnvStore_init():
    store = WindowsEnvStore()
    assert store.env is not None

def test_WindowsEnvStore_load():
    store = WindowsEnvStore()
    store.load()

    assert len(store.env.system) != 0
    assert len(store.env.user) != 0

