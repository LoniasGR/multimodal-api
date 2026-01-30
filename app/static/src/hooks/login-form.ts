import { createFormHook } from '@tanstack/react-form'

import {
  SubmitButton,
  TextField,
} from '../components/forms/forms-components'
import { fieldContext, formContext } from './form-context'

export const { useAppForm } = createFormHook({
  fieldComponents: {
    TextField,
  },
  formComponents: {
    SubmitButton,
  },
  fieldContext,
  formContext,
})