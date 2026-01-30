import { useUser } from "@/context/UserContext";
import { useAppForm } from "@/hooks/login-form";

function LoginPrompt() {
	const {login, } = useUser();
	const defaultValues = {
		username: "",
		password: "",
	};

	const form = useAppForm({
		defaultValues: defaultValues,
		onSubmit: async ({ value }) => {
			alert(JSON.stringify(value, null, 2));
			login(value.username, value.password);
		},
	});

	return (
		<form
			className="leaflet-overlay-pane relative w-xs bg-white mt-2 ml-2 pointer-events-auto"
			onSubmit={(e) => {
				e.preventDefault();
				form.handleSubmit();
			}}
		>
			Please Login
			<form.AppField name="username">
				{(field) => <field.TextField label="Username" />}
			</form.AppField>
			<form.AppField name="password">
				{(field) => <field.TextField type="password" label="Password" />}
			</form.AppField>
            <form.AppForm>
				<div className="flex pb-2">
					<form.SubmitButton label="Login" />
				</div>
			</form.AppForm>
		</form>
	);
}

export default LoginPrompt;
