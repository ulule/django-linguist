VAGRANTFILE_API_VERSION = '2'

VBOXES_PATH = ENV['VBOXES_PATH'] || Pathname.new(ENV['HOME']).join('vboxes')

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "file://#{VBOXES_PATH}/django_linguist.box"
  config.vm.network :forwarded_port, guest: 8000, host: 1337
end
