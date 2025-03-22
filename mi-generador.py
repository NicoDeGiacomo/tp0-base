import sys
from jinja2 import Environment, FileSystemLoader


def main(output_file: str, n_clients: int):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("docker-compose-dev.yaml.jinja")
    output = template.render(n_clients=n_clients)

    with open(output_file, "w") as f:
        f.write(output)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 mi-generador.py <output_file> <n_clients>")
        sys.exit(1)

    _output_file = sys.argv[1]
    _n_clients = int(sys.argv[2])

    main(_output_file, _n_clients)
