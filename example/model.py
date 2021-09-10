

def model(x, y, params):
    """a 2D quadratic test model

    :param x: the x coordinate
    :param y: the y coordinate
    :param params: dictionary of parameters
    :type params: dict
    :return: the z value
    """
    return (params['a'] * x * x +  # noqa: W504
            params['b'] * y * y +  # noqa: W504
            params['c'] * x * y +  # noqa: W504
            params['d'] * x +      # noqa: W504
            params['e'] * y +      # noqa: W504
            params['f'])


if __name__ == '__main__':
    import OptClim2
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path,
                        help='name of configuration file')
    parser.add_argument('output', type=Path,
                        help='name of output file')

    args = parser.parse_args()

    cfg = OptClim2.OptclimConfig(args.config)

    with args.output.open('w') as output:
        for y in range(100):
            y = y - 50
            for x in range(100):
                x = x - 50
                output.write('{0} {1} {2}\n'.format(
                    x, y, model(x, y, cfg.parameters)))
