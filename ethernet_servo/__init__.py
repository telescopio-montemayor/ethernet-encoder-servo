__version__ = '0.0.4'
__all__ = ['api', 'control', 'ethernet_encoder_servo']


def main():
    from .ethernet_encoder_servo import main
    main()
