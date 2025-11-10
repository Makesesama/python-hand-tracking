{ lib
, buildPythonPackage
, fetchFromGitHub
, setuptools
, wheel
, cffi
, pythonOlder
, leapc_cffi
}:

buildPythonPackage rec {
  pname = "leap";
  version = "0.0.1";
  pyproject = true;

  disabled = pythonOlder "3.8";

  src = fetchFromGitHub {
    owner = "ultraleap";
    repo = "leapc-python-bindings";
    rev = "main";  # You can pin this to a specific commit hash for reproducibility
    hash = "sha256-BPDVqUrHnCzY5BKMsMBafLU3oGNN+Qkvi5E6g5wpTNg=";  # Add the hash after first build attempt
  };

  sourceRoot = "${src.name}/leapc-python-api";

  # Patch to use leapc_cffi as a proper Python package instead of filesystem lookup
  patches = [ ./use-packaged-cffi.patch ];

  nativeBuildInputs = [
    setuptools
    wheel
  ];

  propagatedBuildInputs = [
    cffi
    leapc_cffi
  ];

  # The package expects pre-compiled leapc_cffi modules from the Ultraleap Gemini installation
  # We need to ensure LEAPSDK_INSTALL_LOCATION is set if not using default location
  postInstall = ''
    # The package will use pre-compiled modules from Ultraleap Gemini installation (5.17+)
    # No additional compilation needed if using bundled modules
  '';

  # Skip tests as they require Ultraleap hardware and service
  doCheck = false;

  # Skip import check because it requires the Ultraleap service to be installed
  # The module will work fine at runtime when the service is available
  pythonImportsCheck = [ ];

  meta = with lib; {
    description = "Python wrappers around LeapC bindings for Ultraleap hand tracking";
    homepage = "https://github.com/ultraleap/leapc-python-bindings";
    license = licenses.asl20;
    maintainers = [ ];
    platforms = platforms.linux ++ platforms.darwin;
  };
}
