from pyflowmeter.sniffer import create_sniffer

sniffer = create_sniffer(
            input_file='network.pcap',
            to_csv=True,
            output_file='./flows_test.csv',
        )

sniffer.start()
try:
    sniffer.join()
except KeyboardInterrupt:
    print('Stopping the sniffer')
    sniffer.stop()
finally:
    sniffer.join()