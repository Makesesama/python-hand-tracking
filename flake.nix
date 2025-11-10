{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.nixpkgs-ultraleap.url = "github:NixOS/nixpkgs/7a7d128";  # PR #310138 - ultraleap packages
  inputs.systems.url = "github:nix-systems/default";

  outputs =
    { nixpkgs, nixpkgs-ultraleap, systems, ... }:
    let
      eachSystem = nixpkgs.lib.genAttrs (import systems);
      pkgsFor = eachSystem (
        system:
        import nixpkgs {
          localSystem = system;
        }
      );

      # Import ultraleap packages from the PR branch
      # Allow unfree packages for ultraleap-hand-tracking-service
      pkgsUltraleap = eachSystem (
        system:
        import nixpkgs-ultraleap {
          localSystem = system;
          config.allowUnfree = true;
        }
      );

      # Custom packages for Ultraleap bindings
      leapc-cffi = system: pkgsFor.${system}.python312Packages.callPackage ./leapc-cffi.nix {
        ultraleap-hand-tracking-service = pkgsUltraleap.${system}.ultraleap-hand-tracking-service;
      };

      leapc-python-api = system: pkgsFor.${system}.python312Packages.callPackage ./leapc-python-api.nix {
        leapc_cffi = leapc-cffi system;
      };

      pythonPackages = system:
        p: with p; [
          python-lsp-server
          pylsp-mypy
          pyls-isort
          python-lsp-ruff

          pipx
          pip

          # Ultraleap dependencies
          build
          cffi
          numpy

          # OpenCV with GUI support
          (opencv4.override { enableGtk3 = true; })

          # Custom leapc-python-api package
          (leapc-python-api system)
        ];
    in
    {
      devShells = eachSystem (system: {
        default = pkgsFor.${system}.mkShell {
          packages = with pkgsFor.${system}; [
            (python312.withPackages (pythonPackages system))
            ruff
          ];
        };
      });

      # Expose packages for direct installation
      packages = eachSystem (system: {
        leapc-cffi = leapc-cffi system;
        leapc-python-api = leapc-python-api system;
        default = leapc-python-api system;
      });
    };
}
