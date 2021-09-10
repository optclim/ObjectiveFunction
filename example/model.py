

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
    import pandas
    import numpy

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path,
                        help='name of configuration file')
    parser.add_argument('-s', '--scale', type=float, default=10,
                        help="scale for random noise to add to synthetic data")
    parser.add_argument('-g', '--generate', action='store_true', default=False,
                        help="generate synthetic data")

    args = parser.parse_args()

    cfg = OptClim2.OptclimConfig(args.config)

    dname = cfg.basedir / 'synthetic.data'
    if args.generate:
        with dname.open('w') as output:
            for y in range(100):
                y = y - 50
                for x in range(100):
                    x = x - 50
                    output.write('{0},{1},{2}\n'.format(
                        x, y, model(x, y, cfg.parameters) +  # noqa: W504
                        numpy.random.normal(scale=args.scale)))
    else:
        objfun = cfg.objectiveFunction
        try:
            params = objfun.get_new()
        except Exception as e:
            parser.error(e)

        data = pandas.read_csv(dname, names=['x', 'y', 'z'])

        # compute model values for parameter
        data['computed'] = data.apply(lambda row:
                                      model(row['x'], row['y'], params),
                                      axis=1)

        # compute difference between observation and model
        data['diff'] = data['computed'] - data['z']
        # and standard devation
        std = data['diff'].std()

        objfun.set_result(params, std)
