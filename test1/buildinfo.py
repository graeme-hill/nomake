def get_config():
	return (
		Platform(name='mac', modules=('mac', 'real_io')),
		Platform(name='windows', modules=('windows', 'real_io')),
		Platform(name='mac_test', modules=('mac_test', 'fake_io'))
	)