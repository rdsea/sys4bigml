#!/bin/bash
# # remember docker login to authentication the docekrHUB
# username="hongtringuyen"
#
# for dir in $(ls -d */); do
# 	if [ -f "$dir/Dockerfile" ]; then
# 		echo "Dockerfile found in $dir. Building and pushing Docker image."
# 		docker build -t "$username/$(basename $dir)" "$dir"
# 		docker push "$username/$(basename $dir)"
# 	else
# 		echo "No Dockerfile found in $dir. Skipping build and push."
# 	fi
# done
#!/bin/bash
# remember docker login to authentication the docekrHUB
#username="hongtringuyen"
#username=$1 # Replace with your Docker username
#yaml_folder=$2

username=$1    # Replace with your Docker username
yaml_folder=$2 # Folder containing the YAML files
image_map=()

# Check if the YAML folder is provided
if [ -z "$yaml_folder" ]; then
	echo "Usage: $0 <yaml-folder>"
	exit 1
fi

# Ensure the provided folder exists
if [ ! -d "$yaml_folder" ]; then
	echo "The specified YAML folder does not exist: $yaml_folder"
	exit 1
fi

# Loop through directories and build/push Docker images
for dir in $(ls -d */); do
	dirname=$(basename "$dir" | tr -d '/')
	if [ -f "$dir/Dockerfile" ]; then
		echo "Dockerfile found in $dir. Building and pushing Docker image."
		imagename="$username/$dirname"
		docker build -t "$imagename" "$dir"
		docker push "$imagename"

		# Check and update corresponding YAML file
		yaml_file="$yaml_folder/$dirname.yml"
		if [ -f "$yaml_file" ]; then
			echo "Updating image in $yaml_file."
			old_image=$(grep -oP 'image: \K.*' "$yaml_file")
			if [ ! -z "$old_image" ]; then
				echo "Replacing $old_image with $imagename in $yaml_file."
				sed -i.bak 's#image: '"$old_image"'#image: '"$imagename"'#' "$yaml_file"
				rm "$yaml_file.bak"
			else
				echo "No image found in $yaml_file. Skipping."
			fi
		else
			echo "No YAML file named $dirname.yml found in $yaml_folder. Skipping."
		fi
	else
		echo "No Dockerfile found in $dir. Skipping build and push."
	fi
done
