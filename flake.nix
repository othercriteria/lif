{
  description = "Lif - Game of Life variant with local dynamics";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            python3Packages.virtualenv
            python3Packages.pip
            python3Packages.setuptools
          ];

          shellHook = ''
            # Create a virtual environment if it doesn't exist
            if [ ! -d .venv ]; then
              echo "Creating virtual environment..."
              virtualenv .venv
            fi
            
            # Activate the virtual environment
            source .venv/bin/activate
            
            # Install the package in development mode
            pip install -e .
            
            # Setup prompt
            export PS1="\n\[\033[1;32m\][lif:\[\033[1;34m\]\w\[\033[1;32m\]]\$\[\033[0m\] "
            
            echo "Lif development environment activated!"
            echo "Run 'deactivate' to exit the virtual environment"
          '';
        };
      }
    );
}