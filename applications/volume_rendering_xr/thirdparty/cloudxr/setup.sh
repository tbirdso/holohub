
# Create a temporary directory for logs
TMP_DIR=$(mktemp -d)
echo "Temporary directory: ${TMP_DIR}"

mkdir -p ${TMP_DIR}/cloudxr
docker run --name cloudxr-runtime \
    --user $(id -u):$(id -g) \
    --gpus=all \
    -e "ACCEPT_EULA=Y" \
    --mount type=bind,src=${SCRIPT_DIR}/openxr,dst=/openxr \
    -p 48010:48010 \
    -p 47998:47998/udp \
    -p 47999:47999/udp \
    -p 48000:48000/udp \
    -p 48005:48005/udp \
    -p 48008:48008/udp \
    -p 48012:48012/udp \
    nvcr.io/nvidia/cloudxr-runtime:0.1.0-isaac > "$TMP_DIR/cloudxr.log" 2>&1 
echo "CloudXR runtime started"

export XDG_RUNTIME_DIR=${TMP_DIR}/cloudxr/run
export XR_RUNTIME_JSON=${TMP_DIR}/cloudxr/share/openxr/1/openxr_cloudxr.json

# Launch default container
./holohub run-container \
    --docker_opts "-e XDG_RUNTIME_DIR -e XR_RUNTIME_JSON"
# TODO: expose interface to run command in holohub container
# ./holohub run volume_rendering_xr