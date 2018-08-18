from vesync import VeSync

manager = VeSync("jtrabulsy@gmail.com", "Microsoft1!")
manager.login()
manager.update()

print(manager.devices[1].device_name)
print(' ')
print(manager.devices[1].get_power())
print(manager.devices[1].get_voltage())