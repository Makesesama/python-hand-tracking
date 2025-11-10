{ lib
, buildPythonPackage
, fetchFromGitHub
, setuptools
, wheel
, cffi
, pythonOlder
, ultraleap-hand-tracking-service
}:

buildPythonPackage rec {
  pname = "leapc_cffi";
  version = "0.0.1";
  pyproject = true;

  disabled = pythonOlder "3.8";

  src = fetchFromGitHub {
    owner = "ultraleap";
    repo = "leapc-python-bindings";
    rev = "main";
    hash = "sha256-BPDVqUrHnCzY5BKMsMBafLU3oGNN+Qkvi5E6g5wpTNg=";
  };

  sourceRoot = "${src.name}/leapc-cffi";

  # Patch to skip file copying in setup.py since we pre-populate files
  patches = [ ./skip-file-copy.patch ];

  # Make the source writable
  postUnpack = ''
    chmod -R +w "${src.name}"
  '';

  # Pre-copy required files that setup.py needs
  postPatch = ''
    # Pre-populate the files that setup.py would normally copy/symlink
    mkdir -p src/leapc_cffi
    cp "${ultraleap-hand-tracking-service}/lib/leapc_cffi/LeapC.h" src/leapc_cffi/
    cp "${ultraleap-hand-tracking-service}/lib/libLeapC.so" src/leapc_cffi/
    cp "${ultraleap-hand-tracking-service}/lib/libLeapC.so.5" src/leapc_cffi/
    # Create symlink that setup.py would create
    ln -sf libLeapC.so.5 src/leapc_cffi/libLeapC.so
  '';

  nativeBuildInputs = [
    setuptools
    wheel
    cffi
  ];

  propagatedBuildInputs = [
    cffi
  ];

  buildInputs = [
    ultraleap-hand-tracking-service
  ];

  # Set environment variables for build
  preBuild = ''
    export LEAPSDK_INSTALL_LOCATION="${ultraleap-hand-tracking-service}"
    export LEAPC_HEADER_OVERRIDE="${ultraleap-hand-tracking-service}/lib/leapc_cffi/LeapC.h"
    export LEAPC_LIB_OVERRIDE="${ultraleap-hand-tracking-service}/lib/libLeapC.so"
  '';

  # Skip tests as they require Ultraleap hardware and service
  doCheck = false;

  # Skip import check - will be tested by leapc-python-api
  pythonImportsCheck = [ ];

  meta = with lib; {
    description = "CFFI bindings for LeapC library";
    homepage = "https://github.com/ultraleap/leapc-python-bindings";
    license = licenses.asl20;
    maintainers = [ ];
    platforms = platforms.linux ++ platforms.darwin;
  };
}
